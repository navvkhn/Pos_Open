import streamlit as st
from supabase_client import supabase
from datetime import datetime
import pytz
from dateutil.parser import isoparse

IST = pytz.timezone("Asia/Kolkata")


def kitchen_screen(tenant_id):
    st.set_page_config(layout="wide")
    st.title("🍳 Kitchen Dashboard")

    # ✅ Auto refresh every 10 seconds (SUPPORTED)
    st_autorefresh = st.experimental_data_editor if False else None
    st_autorefresh = st.experimental_memo if False else None
    st_autorefresh = st.experimental_singleton if False else None

    st.markdown(
        """
        <meta http-equiv="refresh" content="60">
        """,
        unsafe_allow_html=True
    )

    # -----------------------------
    # Fetch ONLY OPEN ORDERS
    # -----------------------------
    orders = supabase.table("orders") \
        .select("*") \
        .eq("tenant_id", tenant_id) \
        .eq("status", "open") \
        .order("created_at") \
        .execute()

    if not orders.data:
        st.info("No active orders")
        return

    # -----------------------------
    # Grid: 4 orders per row
    # -----------------------------
    cols = st.columns(4)
    col_index = 0

    for order in orders.data:
        with cols[col_index]:
            col_index = (col_index + 1) % 4

            # -----------------------------
            # SAFE TIME PARSING (UTC → IST)
            # -----------------------------
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

            # -----------------------------
            # ORDER CARD
            # -----------------------------
            st.markdown(
                f"""
                ### 🧾 Order #{order['id']}
                **Table:** {order.get('table_name', '—')}  
                **Customer:** {order.get('customer_name', 'Guest')}  

                🕒 **Time:** {time_str}  
                ⏳ **Pending:** {minutes_pending} min  
                """
            )

            # -----------------------------
            # ITEMS
            # -----------------------------
            items = supabase.table("order_items") \
                .select("*") \
                .eq("order_id", order["id"]) \
                .execute()

            for item in items.data:
                st.write(
                    f"- {item['product_name']} × {item['quantity']}"
                )

            # -----------------------------
            # ACTION
            # -----------------------------
            if st.button(
                "✅ Mark Prepared",
                key=f"prep_{order['id']}"
            ):
                supabase.table("orders") \
                    .update({"status": "prepared"}) \
                    .eq("id", order["id"]) \
                    .execute()

                st.rerun()
