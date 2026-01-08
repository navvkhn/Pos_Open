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
        with st.expander(f"Order #{order['id']} — ₹{order['total']}"):
            st.write(f"Payment Status: {order['payment_status']}")
            st.write(f"Order Status: {order['status']}")

            if order["payment_status"] == "pending":
                if st.button(f"Mark Paid (Order {order['id']})"):
                    supabase.table("orders") \
                        .update({"payment_status": "paid"}) \
                        .eq("id", order["id"]) \
                        .execute()
                    st.success("Payment marked as PAID")
                    st.rerun()

            if order["status"] == "open":
                if st.button(f"Close Order {order['id']}"):
                    supabase.table("orders") \
                        .update({"status": "completed"}) \
                        .eq("id", order["id"]) \
                        .execute()
                    st.success("Order completed")
                    st.rerun()
