import streamlit as st
from supabase_client import supabase
from datetime import datetime
import pytz

IST = pytz.timezone("Asia/Kolkata")


def reception_screen(tenant_id):
    st.title("🧾 Reception")

    today_utc = datetime.now(IST).replace(
        hour=0, minute=0, second=0, microsecond=0
    ).astimezone(pytz.utc)

    orders = supabase.table("orders") \
        .select("*, order_items(*)") \
        .eq("tenant_id", tenant_id) \
        .gte("created_at", today_utc.isoformat()) \
        .order("created_at", desc=True) \
        .execute()

    for order in orders.data:
        with st.expander(
            f"Order #{order.get('order_number')} | ₹{order['total']} | {order.get('customer_name')}"
        ):
            table = st.text_input(
                "Table",
                value=order.get("table_name",""),
                key=f"t{order['id']}"
            )

            if st.button("Save", key=f"s{order['id']}"):
                supabase.table("orders") \
                    .update({"table_name": table}) \
                    .eq("id", order["id"]) \
                    .execute()
                st.rerun()

            if st.button("Paid", key=f"pay{order['id']}"):
                supabase.table("orders") \
                    .update({"payment_status": "paid"}) \
                    .eq("id", order["id"]) \
                    .execute()
                st.rerun()

            if st.button("Close", key=f"c{order['id']}"):
                supabase.table("orders") \
                    .update({"status": "completed"}) \
                    .eq("id", order["id"]) \
                    .execute()
                st.rerun()
