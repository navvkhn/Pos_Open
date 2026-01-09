import streamlit as st
from datetime import datetime, timezone
from dateutil import parser as date_parser
from db.game import add_game, get_active_games, end_game, update_game
from db.table import get_tables
from db.customer import get_customers, add_customer

st.set_page_config(page_title="Reception - POS", layout="wide")


def parse_utc(dt):
    """Parse datetime from various formats"""
    if isinstance(dt, datetime):
        return dt
    if dt is None:
        return None
    try:
        return date_parser.parse(str(dt))
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid datetime format: {dt} (type: {type(dt)}). Error: {e}")


def format_duration(minutes):
    """Format minutes into hours and minutes"""
    if minutes < 60:
        return f"{minutes}m"
    hours = minutes // 60
    mins = minutes % 60
    if mins == 0:
        return f"{hours}h"
    return f"{hours}h {mins}m"


def calculate_game_amount(game):
    """Calculate game amount based on elapsed time"""
    start = parse_utc(game["start_time"])
    now = datetime.now(timezone.utc)
    elapsed = now - start
    elapsed_min = int(elapsed.total_seconds() / 60)
    
    rate_hr = game.get("rate_per_hour", 0)
    
    # Calculate billed minutes (round up to nearest 15 min)
    billed_min = ((elapsed_min + 14) // 15) * 15
    
    # Calculate amount
    game_amount = (billed_min / 60) * rate_hr
    
    return elapsed_min, billed_min, rate_hr, game_amount


def reception_screen(tenant_id):
    st.title("🎮 Reception - Game Management")
    
    # Sidebar for starting new games
    with st.sidebar:
        st.header("Start New Game")
        
        # Get available tables
        tables = get_tables(tenant_id)
        available_tables = [t for t in tables if t.get("status") == "available"]
        
        if not available_tables:
            st.warning("No tables available")
        else:
            table_options = {f"Table {t['table_number']}": t["id"] for t in available_tables}
            selected_table = st.selectbox("Select Table", options=list(table_options.keys()))
            
            # Customer selection
            customers = get_customers(tenant_id)
            customer_options = ["Walk-in"] + [f"{c['name']} - {c['phone']}" for c in customers]
            selected_customer = st.selectbox("Customer", customer_options)
            
            # Add new customer option
            if st.checkbox("Add New Customer"):
                with st.form("new_customer_form"):
                    new_name = st.text_input("Customer Name")
                    new_phone = st.text_input("Phone Number")
                    new_email = st.text_input("Email (optional)")
                    
                    if st.form_submit_button("Add Customer"):
                        if new_name and new_phone:
                            add_customer(tenant_id, new_name, new_phone, new_email if new_email else None)
                            st.success(f"Customer {new_name} added!")
                            st.rerun()
                        else:
                            st.error("Name and phone are required")
            
            # Game type and rate
            game_type = st.selectbox("Game Type", ["Pool", "Snooker", "Carrom", "Other"])
            rate = st.number_input("Rate per Hour (₹)", min_value=0, value=100, step=10)
            
            # Notes
            notes = st.text_area("Notes (optional)")
            
            if st.button("🎯 Start Game", type="primary", use_container_width=True):
                table_id = table_options[selected_table]
                
                # Get customer ID if not walk-in
                customer_id = None
                if selected_customer != "Walk-in":
                    customer_phone = selected_customer.split(" - ")[1]
                    customer = next((c for c in customers if c["phone"] == customer_phone), None)
                    if customer:
                        customer_id = customer["id"]
                
                # Start the game
                game_id = add_game(
                    tenant_id=tenant_id,
                    table_id=table_id,
                    customer_id=customer_id,
                    game_type=game_type,
                    rate_per_hour=rate,
                    notes=notes
                )
                
                if game_id:
                    st.success(f"Game started on {selected_table}!")
                    st.rerun()
                else:
                    st.error("Failed to start game")
    
    # Main area - Active games
    st.header("🎲 Active Games")
    
    active_games = get_active_games(tenant_id)
    
    if not active_games:
        st.info("No active games at the moment")
    else:
        # Create columns for game cards
        cols_per_row = 3
        for idx in range(0, len(active_games), cols_per_row):
            cols = st.columns(cols_per_row)
            
            for col_idx, game in enumerate(active_games[idx:idx + cols_per_row]):
                with cols[col_idx]:
                    # Calculate current amount
                    elapsed_min, billed_min, rate_hr, game_amount = calculate_game_amount(game)
                    
                    # Create card
                    with st.container(border=True):
                        # Header
                        st.subheader(f"🎱 Table {game['table_number']}")
                        
                        # Game info
                        st.write(f"**Type:** {game['game_type']}")
                        st.write(f"**Customer:** {game.get('customer_name', 'Walk-in')}")
                        
                        # Time info
                        start_time = parse_utc(game["start_time"])
                        st.write(f"**Started:** {start_time.strftime('%I:%M %p')}")
                        st.write(f"**Duration:** {format_duration(elapsed_min)}")
                        st.write(f"**Billed:** {format_duration(billed_min)}")
                        
                        # Amount
                        st.metric("Current Amount", f"₹{game_amount:.2f}")
                        
                        # Notes if any
                        if game.get('notes'):
                            with st.expander("📝 Notes"):
                                st.write(game['notes'])
                        
                        # Action buttons
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if st.button("⏸️ Pause", key=f"pause_{game['id']}", use_container_width=True):
                                # Toggle pause status
                                new_status = "paused" if game.get("status") == "active" else "active"
                                update_game(game["id"], {"status": new_status})
                                st.rerun()
                        
                        with col2:
                            if st.button("🛑 End", key=f"end_{game['id']}", type="primary", use_container_width=True):
                                # End the game
                                end_game(game["id"], game_amount)
                                st.success(f"Game ended! Amount: ₹{game_amount:.2f}")
                                st.rerun()
                        
                        # Show pause indicator
                        if game.get("status") == "paused":
                            st.warning("⏸️ Game Paused")
    
    # Quick stats
    st.divider()
    st.subheader("📊 Quick Stats")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Active Games", len(active_games))
    
    with col2:
        total_tables = len(tables)
        occupied = len([t for t in tables if t.get("status") == "occupied"])
        st.metric("Tables Occupied", f"{occupied}/{total_tables}")
    
    with col3:
        total_revenue = sum(calculate_game_amount(g)[3] for g in active_games)
        st.metric("Current Revenue", f"₹{total_revenue:.2f}")


if __name__ == "__main__":
    # For testing
    reception_screen("test_tenant")
