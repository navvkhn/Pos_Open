import streamlit as st
from supabase_client import supabase

# -------------------------
# AUTH & PAGES
# -------------------------
from auth import login
from admin.products import products
from admin.reports import reports
from admin.settings import settings

from customer.menu import customer_menu
from customer.payment import payment_page

from kitchen.kitchen import kitchen_screen
from reception.reception import reception_screen

from utils.qr import generate_qr

# --------------------------------------------------
# APP CONFIG
# --------------------------------------------------
st.set_page_config(
    page_title="Superscale POS",
    layout="wide"
)

APP_URL = st.secrets.get(
    "APP_URL",
    "https://posbynaved.streamlit.app"
)

query = st.query_params

# --------------------------------------------------
# 🌐 PUBLIC ROUTES (NO LOGIN REQUIRED)
# --------------------------------------------------

# 1️⃣ CUSTOMER QR MENU
if "menu" in query:
    customer_menu(query["menu"])
    st.stop()

# 2️⃣ PAYMENT PAGE
if "pay" in query:
    payment_page(int(query["pay"]))
    st.stop()

# 3️⃣ KITCHEN SCREEN (PUBLIC)
if "kitchen" in query:
    try:
        tenant = supabase.table("tenants") \
            .select("id, name, logo_url") \
            .eq("name", query["kitchen"]) \
            .single() \
            .execute()

        if tenant.data:
            # Browser tab icon = cafe logo
            if tenant.data.get("logo_url"):
                st.markdown(
                    f"""
                    <link rel="icon" href="{tenant.data['logo_url']}">
                    """,
                    unsafe_allow_html=True
                )

            kitchen_screen(tenant.data["id"])
        else:
            st.error("Kitchen not found")

    except Exception:
        st.error("Unable to load kitchen screen")

    st.stop()

# 4️⃣ GAMING SCREEN (PUBLIC)
if "gaming" in query:
    try:
        tenant = supabase.table("tenants") \
            .select("id, name, logo_url") \
            .eq("name", query["gaming"]) \
            .single() \
            .execute()

        if tenant.data:
            if tenant.data.get("logo_url"):
                st.markdown(
                    f"""
                    <link rel="icon" href="{tenant.data['logo_url']}">
                    """,
                    unsafe_allow_html=True
                )

            from gaming.gaming import gaming_screen
            gaming_screen(tenant.data["id"])
        else:
            st.error("Gaming screen not found")

    except Exception:
        st.error("Unable to load gaming screen")

    st.stop()

# --------------------------------------------------
# 🔐 ADMIN FLOW (LOGIN REQUIRED)
# --------------------------------------------------
if "user" not in st.session_state:
    login()
    st.stop()

# --------------------------------------------------
# 👤 LOGGED-IN USER CONTEXT
# --------------------------------------------------
tenant_id = st.session_state.user["tenant_id"]
tenant_name = st.session_state.user["tenant"]

# --------------------------------------------------
# 🎨 TENANT BRANDING (LOGO AS TAB ICON)
# --------------------------------------------------
try:
    tenant = supabase.table("tenants") \
        .select("logo_url") \
        .eq("id", tenant_id) \
        .single() \
        .execute()

    if tenant.data and tenant.data.get("logo_url"):
        st.markdown(
            f"""
            <link rel="icon" href="{tenant.data['logo_url']}">
            """,
            unsafe_allow_html=True
        )
except Exception:
    pass

# --------------------------------------------------
# 📚 SIDEBAR
# --------------------------------------------------
st.sidebar.title(tenant_name)

# ---- LOGOUT ----
if st.sidebar.button("🚪 Logout"):
    st.session_state.clear()
    st.rerun()

# ---- CUSTOMER QR MENU ----
with st.sidebar.expander("📱 Customer QR Menu"):
    menu_url = f"{APP_URL}/?menu={tenant_name.replace(' ', '%20')}"
    qr_img = generate_qr(menu_url)
    st.image(qr_img, caption="Scan to open menu")
    st.code(menu_url)

# ---- KITCHEN SCREEN ----
with st.sidebar.expander("🍳 Kitchen Screen"):
    kitchen_url = f"{APP_URL}/?kitchen={tenant_name.replace(' ', '%20')}"
    st.code(kitchen_url)
    st.caption("Open this on kitchen tablet / TV")

# ---- GAMING SCREEN ----
with st.sidebar.expander("🎱 Gaming Screen"):
    gaming_url = f"{APP_URL}/?gaming={tenant_name.replace(' ', '%20')}"
    st.code(gaming_url)
    st.caption("Open this near pool table")

# --------------------------------------------------
# 🧭 NAVIGATION
# --------------------------------------------------
page = st.sidebar.selectbox(
    "Menu",
    ["Products", "Reports", "Reception", "Settings"]
)

# --------------------------------------------------
# 📄 PAGE ROUTING
# --------------------------------------------------
if page == "Products":
    products(tenant_id)

elif page == "Reports":
    reports(tenant_id)

elif page == "Reception":
    reception_screen(tenant_id)

elif page == "Settings":
    settings(tenant_id)
