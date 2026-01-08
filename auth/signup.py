import streamlit as st
from db import SessionLocal
from models import Tenant, User
from passlib.hash import pbkdf2_sha256

def signup():
    st.title("📝 Restaurant Signup")

        restaurant = st.text_input("Restaurant Name", key="signup_restaurant")
        username = st.text_input("Admin Username", key="signup_username")
        password = st.text_input("Password", type="password", key="signup_password")
        confirm = st.text_input("Confirm Password", type="password", key="signup_confirm")


    if st.button("Create Account"):
        if not restaurant or not username or not password:
            st.error("All fields are required")
            return

        if password != confirm:
            st.error("Passwords do not match")
            return

        db = SessionLocal()

        # Check if tenant exists
        existing = db.query(Tenant).filter(Tenant.name == restaurant).first()
        if existing:
            st.error("Restaurant already exists")
            return

        # Create tenant
        tenant = Tenant(name=restaurant)
        db.add(tenant)
        db.commit()
        db.refresh(tenant)

        # Create admin user
        hashed = pbkdf2_sha256.hash(password)
        user = User(
            tenant_id=tenant.id,
            username=username,
            password=hashed,
            role="admin"
        )

        db.add(user)
        db.commit()

        # Auto login
        st.session_state.user = {
            "username": username,
            "role": "admin",
            "tenant_id": tenant.id,
            "tenant": tenant.name
        }

        st.success("🎉 Account created successfully")
        st.rerun()
