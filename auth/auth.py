import streamlit as st
from supabase_client import supabase
from passlib.hash import pbkdf2_sha256
from .signup import signup

def login():
    st.title("🔐 Superscale POS Login")

    tab1, tab2 = st.tabs(["Login", "Signup"])

    with tab1:
        # -----------------------------
        # Fetch restaurants
        # -----------------------------
        tenants = supabase.table("tenants") \
            .select("id,name") \
            .order("name") \
            .execute()

        if not tenants.data:
            st.warning("No restaurants found. Please sign up.")
            return

        tenant_map = {t["name"]: t["id"] for t in tenants.data}

        restaurant = st.selectbox(
            "Select Restaurant",
            options=list(tenant_map.keys())
        )

        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            tenant_id = tenant_map[restaurant]

            user = supabase.table("users") \
                .select("*") \
                .eq("tenant_id", tenant_id) \
                .eq("username", username) \
                .execute()

            if not user.data:
                st.error("Invalid credentials")
                return

            if not pbkdf2_sha256.verify(password, user.data[0]["password"]):
                st.error("Invalid credentials")
                return

            # -----------------------------
            # Login success
            # -----------------------------
            st.session_state.user = {
                "tenant_id": tenant_id,
                "tenant": restaurant,
                "username": username,
                "role": user.data[0]["role"]
            }

            st.success("Logged in successfully")
            st.rerun()

    with tab2:
        signup()
