import streamlit as st
from supabase_client import supabase
from datetime import datetime
import pytz
import time

IST = pytz.timezone("Asia/Kolkata")
time.sleep(0.2)

# --------------------------------------------------
# 🧠 HELPERS
# --------------------------------------------------
def calculate_game_amount(game):
    """Calculate game amount with proper datetime parsing"""
    try:
        # Parse start_time - handle various formats
        start_str = game["start_time"]
        if isinstance(start_str, str):
            # Remove 'Z' suffix and parse
            start_str = start_str.replace("Z", "")
            if "+" in start_str:
                # Has timezone offset like +00:00
                start_str = start_str.split("+")[0]
            start = datetime.fromisoformat(start_str)
        else:
            start = start_str
        
        # Make sure start is timezone-aware (UTC)
        if start.tzinfo is None:
            start = start.replace(tzinfo=pytz.UTC)
        
        # Get end time
        end = datetime.now(pytz.UTC)
        
        paused_seconds = game.get("paused_seconds", 0)
        
        # If game is paused, use paused_at time
        if game.get("status") == "paused" and game.get("paused_at"):
            paused_str = game["paused_at"]
            if isinstance(paused_str, str):
                paused_str = paused_str.replace("Z", "")
                if "+" in paused_str:
                    paused_str = paused_str.split("+")[0]
                end = datetime.fromisoformat(paused_str)
            else:
                end = paused_str
            
            if end.tzinfo is None:
                end = end.replace(tzinfo=pytz.UTC)
        
        # Calculate elapsed time
        elapsed_seconds = max(0, int((end - start).total_seconds() - paused_seconds))
        
        hours = elapsed_seconds // 3600
        minutes = (elapsed_seconds % 3600) // 60
        seconds = elapsed_seconds % 60
        
        rate = float(game.get("rate_per_hour", 0))
        amount = round((elapsed_seconds / 3600) * rate, 2)
        
        return elapsed_seconds, hours, minutes, seconds, amount
    
    except Exception as e:
        st.error(f"Error calculating game amount: {str(e)}")
        # Also print to help debug
        st.error(f"Game data: start_time={game.get('start_time')}, status={game.get('status')}")
        return 0, 0, 0, 0, 0.0


# --------------------------------------------------
# 🧾 RECEPTION SCREEN
# --------------------------------------------------
def reception_screen(tenant_id):
    st.title("🧾 Reception / Cashier")

    st.markdown("""
    <style>
    .order-box {
        background-color: var(--secondary-background-color);
        border: 1px solid rgba(128,128,128,0.4);
        border-radius: 12px;
        padding: 14px;
        margin-bottom: 16px;
    }
    button { min-height: 46px; font-size: 15px; }
    </style>
    """, unsafe_allow_html=True)

    if st.button("🔄 Refresh"):
        st.rerun()

    # --------------------------------------------------
    # ➕ CREATE NEW ORDER
    # --------------------------------------------------
    st.divider()
    st.subheader("➕ Create New Order")

    c1, c2 = st.columns([3, 1])

    with c1:
        new_table = st.text_input(
            "🽠Table / Customer Name",
            placeholder="Table 5 / Walk-in / Rahul",
            key="new_table"
        )

    with c2:
        if st.button("➕ Create Order", use_container_width=True):
            if new_table.strip():
                supabase.table("orders").insert({
                    "tenant_id": tenant_id,
                    "table_name": new_table,
                    "status": "open",
                    "created_at": datetime.utcnow().isoformat()
                }).execute()

                st.success("Order created")
                st.rerun()
            else:
                st.error("Please enter a table name")

    # --------------------------------------------------
    # 📅 TODAY ORDERS
    # --------------------------------------------------
    today_ist = datetime.now(IST).replace(hour=0, minute=0, second=0, microsecond=0)
    today_utc = today_ist.astimezone(pytz.utc)

    orders = supabase.table("orders") \
        .select("*, order_items(*)") \
        .eq("tenant_id", tenant_id) \
        .gte("created_at", today_utc.isoformat()) \
        .order("created_at", desc=True) \
        .execute()

    products = supabase.table("products") \
        .select("name, price") \
        .eq("tenant_id", tenant_id) \
        .eq("available", True) \
        .execute()

    product_map = {p["name"]: float(p["price"]) for p in products.data}

    if not orders.data:
        st.info("No orders today")
        return

    # --------------------------------------------------
    # 🧾 ORDER LOOP
    # --------------------------------------------------
    for order in orders.data:
        order_id = order["id"]
        is_open = order["status"] == "open"

        with st.expander(f"🧾 Order — {order.get('table_name') or order_id}", expanded=is_open):
            st.markdown("<div class='order-box'>", unsafe_allow_html=True)

            # ---------------- FOOD ----------------
            st.subheader("🍔 Food Items")
            food_total = 0.0

            for item in order.get("order_items", []):
                c = st.columns([4, 1, 1])
                c[0].write(f"{item['product_name']} × {item['quantity']}")
                c[1].write(f"₹{item['price']:.2f}")
                food_total += float(item["price"])

                if is_open and c[2].button("❌", key=f"del_{item['id']}"):
                    supabase.table("order_items").delete().eq("id", item["id"]).execute()
                    st.rerun()

            if is_open and product_map:
                st.divider()
                p1, p2, p3 = st.columns([3, 1, 1])
                prod = p1.selectbox("Add Item", list(product_map.keys()), key=f"p_{order_id}")
                qty = p2.number_input("Qty", 1, step=1, key=f"q_{order_id}")
                if p3.button("Add", key=f"add_{order_id}"):
                    supabase.table("order_items").insert({
                        "order_id": order_id,
                        "product_name": prod,
                        "quantity": qty,
                        "price": qty * product_map[prod]
                    }).execute()
                    st.rerun()

            # ---------------- GAME ----------------
            st.divider()
            st.subheader("🎱 Pool Game")

            game_res = supabase.table("games") \
                .select("*") \
                .eq("order_id", order_id) \
                .order("start_time", desc=True) \
                .limit(1) \
                .execute()

            game = game_res.data[0] if game_res.data else None

            if not game and is_open:
                rate = st.number_input(
                    "Pool Price (₹ / Hour)",
                    min_value=0,
                    step=50,
                    value=200,
                    key=f"rate_{order_id}"
                )

                if st.button("🎱 Start Pool", key=f"start_{order_id}"):
                    supabase.table("games").insert({
                        "tenant_id": tenant_id,
                        "order_id": order_id,
                        "rate_per_hour": rate,
                        "start_time": datetime.utcnow().isoformat(),
                        "paused_seconds": 0,
                        "status": "running"
                    }).execute()
                    st.rerun()

            if game:
                elapsed, h, m, s, game_amount = calculate_game_amount(game)

                col1, col2 = st.columns(2)
                with col1:
                    st.metric("⏱ Duration", f"{h:02d}h {m:02d}m {s:02d}s")
                with col2:
                    st.metric("💰 Game Amount", f"₹{game_amount}")
                
                rate_per_hour = game.get('rate_per_hour', 0)
                st.write(f"💲 Rate: ₹{rate_per_hour} / hour")
                
                # Game control buttons
                if game["status"] == "running":
                    if st.button("⏸️ Pause Game", key=f"pause_{order_id}"):
                        supabase.table("games").update({
                            "status": "paused",
                            "paused_at": datetime.utcnow().isoformat()
                        }).eq("id", game["id"]).execute()
                        st.rerun()
                
                elif game["status"] == "paused":
                    if st.button("▶️ Resume Game", key=f"resume_{order_id}"):
                        # Calculate paused duration and add to total
                        paused_at_str = game.get("paused_at", "")
                        if paused_at_str:
                            paused_at_str = paused_at_str.replace("Z", "")
                            if "+" in paused_at_str:
                                paused_at_str = paused_at_str.split("+")[0]
                            paused_at = datetime.fromisoformat(paused_at_str)
                            if paused_at.tzinfo is None:
                                paused_at = paused_at.replace(tzinfo=pytz.UTC)
                            
                            now = datetime.now(pytz.UTC)
                            pause_duration = int((now - paused_at).total_seconds())
                            
                            supabase.table("games").update({
                                "status": "running",
                                "paused_at": None,
                                "paused_seconds": game.get("paused_seconds", 0) + pause_duration
                            }).eq("id", game["id"]).execute()
                            st.rerun()
                        else:
                            st.error("Cannot resume: paused_at timestamp missing")

            # ---------------- TOTALS ----------------
            st.divider()
            
            game_total = 0.0
            if game:
                _, _, _, _, game_total = calculate_game_amount(game)
            
            grand_total = food_total + game_total
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("🍔 Food Total", f"₹{food_total:.2f}")
            with col2:
                st.metric("🎱 Game Total", f"₹{game_total:.2f}")
            with col3:
                st.metric("💵 Grand Total", f"₹{grand_total:.2f}")

            # ---------------- ACTIONS ----------------
            st.divider()
            
            if is_open:
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("✅ Complete Order", key=f"complete_{order_id}", type="primary", use_container_width=True):
                        supabase.table("orders").update({
                            "status": "completed",
                            "completed_at": datetime.utcnow().isoformat(),
                            "total_amount": grand_total
                        }).eq("id", order_id).execute()
                        
                        # End any running games
                        if game and game["status"] in ["running", "paused"]:
                            supabase.table("games").update({
                                "status": "completed",
                                "end_time": datetime.utcnow().isoformat()
                            }).eq("id", game["id"]).execute()
                        
                        st.success(f"Order completed! Total: ₹{grand_total:.2f}")
                        st.rerun()
                
                with col2:
                    if st.button("🗑 Delete Order", key=f"delete_{order_id}", use_container_width=True):
                        supabase.table("order_items").delete().eq("order_id", order_id).execute()
                        supabase.table("games").delete().eq("order_id", order_id).execute()
                        supabase.table("orders").delete().eq("id", order_id).execute()
                        st.success("Order deleted")
                        st.rerun()
            
            else:
                st.success("✅ Order Completed")

            st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    # For testing
    reception_screen("test_tenant")
