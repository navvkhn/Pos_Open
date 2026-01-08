import streamlit as st
from auth import login
from admin.products import products
from admin.reports import reports

st.set_page_config(page_title="Superscale POS", layout="wide")

if "user" not in st.session_state:
    login()
else:
    tenant_id = st.session_state.user["tenant_id"]
    st.sidebar.title(st.session_state.user["tenant"])

    page = st.sidebar.selectbox(
        "Menu",
        ["Products", "Reports"]
    )

    if page == "Products":
        products(tenant_id)

    if page == "Reports":
        reports(tenant_id)
