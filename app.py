import streamlit as st

from auth import login
from admin.products import products
from admin.reports import reports
from customer.menu import customer_menu
from utils.qr import generate_qr

# --------------------------------------------------
# App config (must be near top)
# --------------------------------------------------
st.set_page_config(page_title="Superscale POS", layout="wide")

APP_URL = st.secrets.get(
    "APP_URL",
    "https://posbynaved.streamlit.app"
)

# --------------------------------------------------
# QR menu routing (CUSTOMER SIDE)
# --------------------------------------------------
query = st.query_params

if "menu" in query:
    customer_menu(query["menu"])
    st.stop()

# --------------------------------------------------
# ADMIN SIDE
# --------------------------------------------------
if "user" not in st.session_state:
    login()
else:
    tenant_id = st.session_state.user["tenant_id"]
    tenant_name = st.session_state.user["tenant"]

    st.sidebar.title(tenant_name)

    # ---- QR MENU ----
    with st.sidebar.expander("📱 Customer QR Menu"):
        menu_url = f"{APP_URL}/?menu={tenant_name.replace(' ', '%20')}"

        qr_img = generate_qr(menu_url)
        st.image(qr_img, caption="Scan to open menu")
        st.code(menu_url)

    # ---- NAVIGATION ----
    page = st.sidebar.selectbox(
        "Menu",
        ["Products", "Reports"]
    )

    if page == "Products":
        products(tenant_id)

    elif page == "Reports":
        reports(tenant_id)
