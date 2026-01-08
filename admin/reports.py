import streamlit as st
from supabase_client import supabase

def reports(tenant_id):
    st.title("📊 Daily Sales")

    orders = supabase.table("orders") \
        .select("total") \
        .eq("tenant_id", tenant_id) \
        .execute()

    total = sum(o["total"] for o in orders.data) if orders.data else 0
    count = len(orders.data)

    st.metric("Revenue", f"₹ {total}")
    st.metric("Orders", count)
