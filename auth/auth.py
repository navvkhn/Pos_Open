import streamlit as st
from db import SessionLocal
from models import User, Tenant
from passlib.hash import pbkdf2_sha256
from .signup import signup

def login():
    st.title("🔐 Login")

    tab1, tab2 = st.tabs(["Login", "Signup"])

    with tab1:
        tenant_name = st.text_input("Restaurant Name")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            db = SessionLocal()
            tenant = db.query(Tenant).filter(Tenant.name == tenant_name).first()

            if not tenant:
                st.error("Restaurant not found")
                return

            user = db.query(User).filter(
                User.username == username,
                User.tenant_id == tenant.id
            ).first()

            if user and pbkdf2_sha256.verify(password, user.password):
                st.session_state.user = {
                    "username": username,
                    "role": user.role,
                    "tenant_id": tenant.id,
                    "tenant": tenant.name
                }
                st.rerun()
            else:
                st.error("Invalid credentials")

    with tab2:
        signup()
