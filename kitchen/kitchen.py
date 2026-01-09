import streamlit as st
from supabase_client import supabase
from datetime import datetime
import pytz
from dateutil.parser import isoparse
import time

IST = pytz.timezone("Asia/Kolkata")


def kitchen_screen(tenant_id):
    st.set_page_config(layout="wide")
    st.title("🍳 Kitchen Dashboard")

    # --------------------------------------------------
    # 🎨 DARK-MODE SAFE CSS
    # --------------------------------------------------
    st.markdown("""
    <style>
    .order-card {
        background-color: var(--secondary-background-color);
        border: 2px solid rgba(128,128,128,0.3);
        border-radius: 14px;
        padding: 14px;
        margin-bottom: 16px;
    }
    .order-card h3 {
        margin-bottom: 6px;
    }
    button {
        min-height: 48px;
        font-size: 16px;
    }
    </style>
    """, unsafe_allow_html=True)

    # --------------------------------------------------
    # 🔄 AUTO REFRESH (EVERY 10s – SAFE)
    # --------------------------------------------------
    if "kitchen_refresh" not in st.session_state:
        st.session_state.kitchen_refresh = time.time()

    if time.time() - st.session_state.kitchen_refresh > 10:
        st.session_state.kitchen_refresh = time.time()
        st.rerun()

    if st.button("🔄 Refresh"):
        st.session_state.kitchen_refresh = time.time()
        st.rerun()

    # --------------------------------------------------
    # 📦 FETCH OPEN ORDERS (TENANT SAFE)
    # --------------------------------------------------
    orders = supabase.table("orders") \
        .select("""
            id,
            order_number,
            table_name,
            customer_name,
            created_at,
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
        st.info("No active orders 🍽️")
        return

    # --------------------------------------------------
    # 📱 RESPONSIVE GRID (KITCHEN-OPTIMIZED)
    # Mobile → 1 column
    # Tablet/Desktop → 2 columns
    # --------------------------------------------------
    is_mobile = st.session_state.get("mobile", False)
    cols_per_row = 1 if is_mobile else 2
    cols = st.columns(cols_per_row)
    col_index = 0

    # --------------------------------------------------
    # 🧾 ORDER CARDS
    # --------------------------------------------------
    for order in orders.data:
        with cols[col_index]:
            col_index = (col_index + 1) % cols_per_row

            # -----------------------------
            # ⏱ TIME (UTC → IST)
            # -----------------------------
            try:
                created_utc = isoparse(order["created_at"])
                created_ist = created_utc.astimezone(IST)
                now_ist = datetime.now(IST)
                minutes_pending = int(
                    (now_ist - created_ist).total_seconds() / 60
                )
                time_str = created_ist.strftime("%d %b %I:%M %p")
            except Exception:
                time_str = "—"
                minutes_pending = "—"

            # -----------------------------
            # 🧾 ORDER NUMBER (TENANT SAFE)
            # -----------------------------
            display_no = order.get("order_number") or order["id"]

            st.markdown(
                f"""
                <div class="order-card">
                <h3>🧾 Order #{display_no}</h3>

                <b>Table:</b> {order.get('table_name', '—')}<br>
                <b>Customer:</b> {order.get('customer_name', 'Guest')}<br><br>

                🕒 <b>Time:</b> {time_str}<br>
                ⏳ <b>Pending:</b> {minutes_pending} min
                <hr>
                """,
                unsafe_allow_html=True
            )

            # -----------------------------
            # 🍽 ITEMS
            # -----------------------------
            for item in order.get("order_items", []):
                st.write(
                    f"• {item['product_name']} × {item['quantity']}"
                )

            st.markdown("</div>", unsafe_allow_html=True)

            # -----------------------------
            # ✅ MARK PREPARED
            # -----------------------------
            if st.button(
                "✅ Mark Prepared",
                key=f"prep_{order['id']}",
                use_container_width=True
            ):
                supabase.table("orders") \
                    .update({"status": "prepared"}) \
                    .eq("id", order["id"]) \
                    .eq("tenant_id", tenant_id) \
                    .execute()

                st.rerun()
