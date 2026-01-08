import streamlit as st
from supabase_client import supabase
from datetime import datetime
import pytz
from dateutil.parser import isoparse

IST = pytz.timezone("Asia/Kolkata")


def kitchen_screen(tenant_id):
    st.title("🍳 Kitchen Dashboard")

    # Auto refresh every 10 seconds
    st.experimental_rerun()
    st.markdown(
        "<meta http-equiv='refresh' content='10'>",
        unsafe_allow_html=True
    )

    orders = supabase.table("orders") \
        .select("*") \
        .eq("tenant_id", tenant_id) \
        .eq("status", "open") \
        .order("created_at") \
        .execute()

    if not orders.data:
        st.info("No active orders")
        return

    # Grid: 4 orders per row
    cols = st.columns(4)
    col_index = 0

    for order in orders.data:
        with cols[col_index]:
            col_index = (col_index + 1) % 4

            # -----------------------------
            # SAFE TIME PARSING
            # -----------------------------
            created_at_raw = order.get("created_at")

            try:
                created_utc = isoparse(created_at_raw)
                created_ist = created_utc.astimezone(IST)
                now_ist = datetime.now(IST)
                minutes_pending = int((now_ist - created_ist).total_seconds() / 60)
            except Exception:
                created_ist = "—"
                minutes_pending = "—"

            st.markdown(
                f"""
                ### 🧾 Order #{order['id']}
                **Table:** {order.get('table_name','—')}  
                **Customer:** {order.get('customer_name','Guest')}  

                ⏰ **Time:** {created_ist.strftime('%d %b %Y, %I:%M %p') if created_ist != '—' else '—'}  
                ⏳ **Pending:** {minutes_pending} min  
                """
            )

            # -----------------------------
            # ORDER ITEMS
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
