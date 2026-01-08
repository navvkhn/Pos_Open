import streamlit as st
from supabase_client import supabase
from datetime import datetime
import pytz
from dateutil.parser import isoparse
import time

IST = pytz.timezone("Asia/Kolkata")


def kitchen_screen(tenant_id):
    st.set_page_config(layout="wide")

    # --------------------------------------------------
    # 🎨 DARK-MODE SAFE RESPONSIVE CSS
    # --------------------------------------------------
    st.markdown("""
    <style>
    .order-card {
        background-color: var(--secondary-background-color);
        border: 1px solid rgba(128,128,128,0.4);
        border-radius: 12px;
        padding: 14px;
        margin-bottom: 16px;
    }
    .order-card h4 {
        margin-bottom: 6px;
    }
    button {
        min-height: 48px;
        font-size: 16px;
    }
    </style>
    """, unsafe_allow_html=True)

    st.title("🍳 Kitchen Dashboard")

    # --------------------------------------------------
    # 🔄 AUTO REFRESH (SAFE)
    # --------------------------------------------------
    if "kitchen_last_refresh" not in st.session_state:
        st.session_state.kitchen_last_refresh = time.time()

    if time.time() - st.session_state.kitchen_last_refresh > 10:
        st.session_state.kitchen_last_refresh = time.time()
        st.rerun()

    if st.button("🔄 Refresh"):
        st.session_state.kitchen_last_refresh = time.time()
        st.rerun()

    # --------------------------------------------------
    # 📦 FETCH ONLY OPEN ORDERS (JOIN ITEMS)
    # --------------------------------------------------
    orders = supabase.table("orders") \
        .select("""
            *,
            order_items (
                product_name,
                quantity
            )
        """) \
        .eq("tenant_id", tenant_id) \
        .eq("status", "open") \
        .order("created_at") \
        .execute()

    if not orders.data:
        st.info("No active orders")
        return

    # --------------------------------------------------
    # 📱 RESPONSIVE GRID (MOBILE SAFE)
    # --------------------------------------------------
    if st.session_state.get("screen_width", 1200) < 700:
        cols_per_row = 1
    elif st.session_state.get("screen_width", 1200) < 1000:
        cols_per_row = 2
    else:
        cols_per_row = 4

    cols = st.columns(cols_per_row)
    col_index = 0

    # --------------------------------------------------
    # 🧾 ORDER CARDS
    # --------------------------------------------------
    for order in orders.data:
        with cols[col_index]:
            col_index = (col_index + 1) % cols_per_row

            created_raw = order.get("created_at")

            try:
                created_utc = isoparse(created_raw)
                created_ist = created_utc.astimezone(IST)
                now_ist = datetime.now(IST)
                minutes_pending = int(
                    (now_ist - created_ist).total_seconds() / 60
                )
                time_str = created_ist.strftime("%d %b %I:%M %p")
            except Exception:
                time_str = "—"
                minutes_pending = "—"

            st.markdown(
                f"""
                <div class="order-card">
                <h4>🧾 Order #{order['id']}</h4>
                <b>Table:</b> {order.get('table_name', '—')}<br>
                <b>Customer:</b> {order.get('customer_name', 'Guest')}<br><br>
                🕒 <b>Time:</b> {time_str}<br>
                ⏳ <b>Pending:</b> {minutes_pending} min
                <hr>
                """,
                unsafe_allow_html=True
            )

            for item in order.get("order_items", []):
                st.write(
                    f"- {item['product_name']} × {item['quantity']}"
                )

            st.markdown("</div>", unsafe_allow_html=True)

            if st.button(
                "✅ Mark Prepared",
                key=f"prep_{order['id']}",
                use_container_width=True
            ):
                supabase.table("orders") \
                    .update({"status": "prepared"}) \
                    .eq("id", order["id"]) \
                    .execute()

                st.rerun()
