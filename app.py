import streamlit as st
from auth import login
from admin.products import products
from admin.reports import reports
from utils.qr import generate_qr
import streamlit as st

APP_URL = st.secrets.get(
    "APP_URL",
    "https://posbynaved.streamlit.app/"
)


st.set_page_config(page_title="Superscale POS", layout="wide")

if "user" not in st.session_state:
    login()
else:
    tenant_id = st.session_state.user["tenant_id"]
    st.sidebar.title(st.session_state.user["tenant"])
    with st.sidebar.expander("📱 Customer QR Menu"):
    tenant = st.session_state.user["tenant"]
    menu_url = f"{APP_URL}/?menu={tenant.replace(' ', '%20')}"

    qr_img = generate_qr(menu_url)
    st.image(qr_img, caption="Scan to open menu")
    st.code(menu_url)


    page = st.sidebar.selectbox(
        "Menu",
        ["Products", "Reports"]
    )

    if page == "Products":
        products(tenant_id)

    if page == "Reports":
        reports(tenant_id)
