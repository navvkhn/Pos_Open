import streamlit as st
from auth import login
from admin.products import products
from admin.discounts import discounts
from admin.reports import reports
from pos.billing import billing
from customer.menu import customer_menu

st.set_page_config(page_title="Superscale POS", layout="wide")

if "user" not in st.session_state:
    login()
else:
    tenant = st.session_state.user["tenant"]
    tenant_id = st.session_state.user["tenant_id"]

    st.sidebar.title(f"🍽 {tenant}")
    page = st.sidebar.selectbox(
        "Menu",
        ["POS Billing", "Products", "Discounts", "Reports", "Customer Menu"]
    )

    if page == "POS Billing":
        billing(tenant_id)
    if page == "Products":
        products(tenant_id)
    if page == "Discounts":
        discounts(tenant_id)
    if page == "Reports":
        reports(tenant_id)
    if page == "Customer Menu":
        customer_menu(tenant_id)
