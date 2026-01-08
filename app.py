import streamlit as st

from auth import login
from admin.products import products
from admin.reports import reports
from admin.settings import settings

from customer.menu import customer_menu
from customer.payment import payment_page

from kitchen.kitchen import kitchen_screen
from reception.reception import reception_screen

from utils.qr import generate_qr
from supabase_client import supabase


# --------------------------------------------------
# App config
# --------------------------------------------------
st.set_page_config(page_title="Superscale POS", layout="wide")

APP_URL = st.secrets.get(
    "APP_URL",
    "https://posbynaved.streamlit.app"
)

query = st.query_params

# --------------------------------------------------
# PUBLIC ROUTES (NO LOGIN)
# --------------------------------------------------

# 1️⃣ Customer QR Menu
if "menu" in query:
    customer_menu(query["menu"])
    st.stop()

# 2️⃣ Payment page
if "pay" in query:
    payment_page(int(query["pay"]))
    st.stop()

# 3️⃣ Kitchen screen (PUBLIC, NO LOGIN)
if "kitchen" in query:
    tenant = supabase.table("tenants") \
        .select("id") \
        .eq("name", query["kitchen"]) \
        .single() \
        .execute()

    if tenant.data:
        kitchen_screen(tenant.data["id"])
    else:
        st.error("Kitchen not found")

    st.stop()

# --------------------------------------------------
# ADMIN FLOW (LOGIN REQUIRED)
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

    # ---- KITCHEN URL (PUBLIC) ----
    with st.sidebar.expander("🍳 Kitchen Screen"):
        kitchen_url = f"{APP_URL}/?kitchen={tenant_name.replace(' ', '%20')}"
        st.code(kitchen_url)
        st.caption("Open this on kitchen tablet / screen")

    # ---- MAIN NAVIGATION ----
    page = st.sidebar.selectbox(
        "Menu",
        ["Products", "Reports", "Reception", "Settings"]
    )

    # ---- PAGE ROUTING ----
    if page == "Products":
        products(tenant_id)

    elif page == "Reports":
        reports(tenant_id)

    elif page == "Reception":
        reception_screen(tenant_id)

    elif page == "Settings":
        settings(tenant_id)
