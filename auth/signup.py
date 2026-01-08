import streamlit as st
from supabase_client import supabase
from passlib.hash import pbkdf2_sha256

def signup():
    st.title("📝 Restaurant Signup")

    restaurant = st.text_input("Restaurant Name", key="signup_restaurant")
    username = st.text_input("Admin Username", key="signup_username")
    password = st.text_input("Password", type="password", key="signup_password")
    confirm = st.text_input("Confirm Password", type="password", key="signup_confirm")

    if st.button("Create Account"):
        if password != confirm:
            st.error("Passwords do not match")
            return

        # Check tenant
        existing = supabase.table("tenants") \
            .select("id") \
            .eq("name", restaurant) \
            .execute()

        if existing.data:
            st.error("Restaurant already exists")
            return

        # Create tenant
        tenant = supabase.table("tenants") \
            .insert({"name": restaurant}) \
            .execute()

        tenant_id = tenant.data[0]["id"]

        # Create admin user
        supabase.table("users").insert({
            "tenant_id": tenant_id,
            "username": username,
            "password": pbkdf2_sha256.hash(password),
            "role": "admin"
        }).execute()

        st.success("Account created. Please login.")
