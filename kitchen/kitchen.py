import streamlit as st
from supabase_client import supabase
from datetime import datetime
import pytz
from dateutil.parser import isoparse

IST = pytz.timezone("Asia/Kolkata")


def kitchen_screen(tenant_id):
    st.title("🍳 Kitchen")

    orders = supabase.table("orders") \
        .select("*, order_items(*)") \
        .eq("tenant_id", tenant_id) \
        .eq("status", "open") \
        .order("created_at") \
        .execute()

    if not orders.data:
        st.info("No active orders")
        return

    cols = st.columns(4)
    i = 0

    for order in orders.data:
        with cols[i % 4]:
            i += 1

            created = isoparse(order["created_at"]).astimezone(IST)
            mins = int((datetime.now(IST) - created).total_seconds() / 60)

            st.markdown(f"""
            ### 🧾 Order #{order.get("order_number")}
            **Table:** {order.get("table_name","—")}  
            **Customer:** {order.get("customer_name","—")}  
            ⏱ {mins} min
            """)

            for item in order["order_items"]:
                st.write(f"- {item['product_name']} × {item['quantity']}")

            if st.button("Prepared", key=f"p{order['id']}"):
                supabase.table("orders") \
                    .update({"status": "prepared"}) \
                    .eq("id", order["id"]) \
                    .execute()
                st.rerun()
