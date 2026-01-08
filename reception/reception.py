import streamlit as st
from supabase_client import supabase

def reception_screen(tenant_id):
    st.title("🧾 Reception / Cashier")

    orders = supabase.table("orders") \
        .select("*") \
        .eq("tenant_id", tenant_id) \
        .order("created_at", desc=True) \
        .execute()

    for order in orders.data:
        with st.expander(
            f"Order #{order['id']} — {order.get('customer_name','')} — ₹{order['total']}"
        ):
            table_name = st.text_input(
                "Table Name / Number",
                value=order.get("table_name", ""),
                key=f"table_{order['id']}"
            )

            if st.button("Save Table", key=f"save_{order['id']}"):
                supabase.table("orders") \
                    .update({"table_name": table_name}) \
                    .eq("id", order["id"]) \
                    .execute()
                st.success("Table assigned")
                st.rerun()

            st.write(f"Payment: {order['payment_status']}")
            st.write(f"Status: {order['status']}")

            if order["payment_status"] == "pending":
                if st.button("Mark Paid", key=f"paid_{order['id']}"):
                    supabase.table("orders") \
                        .update({"payment_status": "paid"}) \
                        .eq("id", order["id"]) \
                        .execute()
                    st.rerun()

            if order["status"] == "open":
                if st.button("Close Order", key=f"close_{order['id']}"):
                    supabase.table("orders") \
                        .update({"status": "completed"}) \
                        .eq("id", order["id"]) \
                        .execute()
                    st.rerun()
