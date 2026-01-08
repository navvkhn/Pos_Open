import streamlit as st
from reportlab.lib.pagesizes import A4
from auth import login
from admin.products import products
from admin.reports import reports
from admin.settings import settings
from customer.menu import customer_menu
from customer.payment import payment_page
from utils.qr import generate_qr

# --------------------------------------------------
# App config
# --------------------------------------------------
st.set_page_config(page_title="Superscale POS", layout="wide")

APP_URL = st.secrets.get(
    "APP_URL",
    "https://posbynaved.streamlit.app"
)

# --------------------------------------------------
# QUERY PARAM ROUTING (CUSTOMER SIDE)
# --------------------------------------------------
query = st.query_params

# 1️⃣ Customer menu (QR)
if "menu" in query:
    customer_menu(query["menu"])
    st.stop()

# 2️⃣ Payment page after order
if "pay" in query:
    payment_page(int(query["pay"]))
    st.stop()

# --------------------------------------------------
# ADMIN FLOW
# --------------------------------------------------
if "user" not in st.session_state:
    login()

else:
    tenant_id = st.session_state.user["tenant_id"]
    tenant_name = st.session_state.user["tenant"]

    # ---- SIDEBAR HEADER ----
    st.sidebar.title(tenant_name)

    # ---- QR MENU ----
    with st.sidebar.expander("📱 Customer QR Menu"):
        menu_url = f"{APP_URL}/?menu={tenant_name.replace(' ', '%20')}"
        qr_img = generate_qr(menu_url)
        st.image(qr_img, caption="Scan to open menu")
        st.code(menu_url)

    # ---- MAIN NAVIGATION ----
    page = st.sidebar.selectbox(
        "Menu",
        ["Products", "Reports", "Settings", "Kitchen", "Reception"]
    )

    # ---- PAGE ROUTING ----
    if page == "Products":
        products(tenant_id)

    elif page == "Reports":
        reports(tenant_id)
    elif page == "Kitchen":
    kitchen_screen(tenant_id)
    
    elif page == "Reception":
    reception_screen(tenant_id)

    elif page == "Settings":
        settings(tenant_id)
