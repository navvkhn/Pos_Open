import streamlit as st
from supabase_client import supabase
from passlib.hash import pbkdf2_sha256
from .signup import signup

def login():
    st.title("🔐 Superscale POS")

    tab1, tab2 = st.tabs(["Login", "Signup"])

    with tab1:
        restaurant = st.text_input("Restaurant Name", key="login_restaurant")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")

        if st.button("Login"):
            tenant = supabase.table("tenants") \
                .select("id,name") \
                .eq("name", restaurant) \
                .execute()

            if not tenant.data:
                st.error("Restaurant not found")
                return

            tenant_id = tenant.data[0]["id"]

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

            st.session_state.user = {
                "tenant_id": tenant_id,
                "tenant": restaurant,
                "username": username,
                "role": user.data[0]["role"]
            }

            st.success("Logged in")
            st.rerun()

    with tab2:
        signup()
