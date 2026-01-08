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
# App config (DEFAULT BEFORE LOGIN)
# --------------------------------------------------
st.set_page_config(
    page_title="Superscale POS",
    page_icon="🍽️",
    layout="wide"
)

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

# 3️⃣ Kitchen screen (PUBLIC)
if "kitchen" in query:
    tenant = supabase.table("tenants") \
        .select("id, name, logo_url") \
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

    # --------------------------------------------------
    # FETCH TENANT (FOR LOGO)
    # --------------------------------------------------
    tenant = supabase.table("tenants") \
        .select("logo_url") \
        .eq("id", tenant_id) \
        .single() \
        .execute()

    logo_url = tenant.data.get("logo_url")

    # --------------------------------------------------
    # SIDEBAR HEADER (LOGO + NAME)
    # --------------------------------------------------
    if logo_url:
        st.sidebar.image(logo_url, width=120)

    st.sidebar.markdown(f"### {tenant_name}")

    # --------------------------------------------------
    # LOGOUT
    # --------------------------------------------------
    if st.sidebar.button("🚪 Logout"):
        st.session_state.clear()
        st.query_params.clear()
        st.rerun()

    st.sidebar.divider()

    # --------------------------------------------------
    # QR MENU
    # --------------------------------------------------
    with st.sidebar.expander("📱 Customer QR Menu"):
        menu_url = f"{APP_URL}/?menu={tenant_name.replace(' ', '%20')}"
        qr_img = generate_qr(menu_url)
        st.image(qr_img, caption="Scan to open menu")
        st.code(menu_url)

    # --------------------------------------------------
    # KITCHEN URL (PUBLIC)
    # --------------------------------------------------
    with st.sidebar.expander("🍳 Kitchen Screen"):
        kitchen_url = f"{APP_URL}/?kitchen={tenant_name.replace(' ', '%20')}"
        st.code(kitchen_url)
        st.caption("Open on kitchen tablet / TV")

    st.sidebar.divider()

    # --------------------------------------------------
    # MAIN NAVIGATION
    # --------------------------------------------------
    page = st.sidebar.selectbox(
        "Menu",
        ["Products", "Reports", "Reception", "Settings"]
    )

    # --------------------------------------------------
    # PAGE HEADER (LOGO ON PAGE)
    # --------------------------------------------------
    if logo_url:
        st.image(logo_url, width=100)

    st.title(tenant_name)

    st.divider()

    # --------------------------------------------------
    # PAGE ROUTING
    # --------------------------------------------------
    if page == "Products":
        products(tenant_id)

    elif page == "Reports":
        reports(tenant_id)

    elif page == "Reception":
        reception_screen(tenant_id)

    elif page == "Settings":
        settings(tenant_id)
