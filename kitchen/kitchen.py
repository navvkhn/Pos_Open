import streamlit as st
from supabase_client import supabase

def kitchen_screen(tenant_id):
    st.title("🍳 Kitchen Orders")

    orders = supabase.table("orders") \
        .select("id, created_at") \
        .eq("tenant_id", tenant_id) \
        .eq("status", "open") \
        .order("created_at") \
        .execute()

    if not orders.data:
        st.info("No active orders")
        return

    for order in orders.data:
        st.subheader(f"Order #{order['id']}")

        items = supabase.table("order_items") \
            .select("*") \
            .eq("order_id", order["id"]) \
            .execute()

        for item in items.data:
            st.write(f"{item['quantity']} × {item['product_name']}")

        st.divider()
