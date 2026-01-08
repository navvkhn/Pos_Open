import streamlit as st
from db import SessionLocal
from models import Order
from sqlalchemy import func
import datetime

def reports(tenant_id):
    st.title("📊 Daily Sales")

    db = SessionLocal()
    today = datetime.date.today()

    revenue = db.query(func.sum(Order.total))\
        .filter(func.date(Order.created_at)==today)\
        .filter(Order.tenant_id==tenant_id)\
        .scalar() or 0

    orders = db.query(Order)\
        .filter(func.date(Order.created_at)==today)\
        .filter(Order.tenant_id==tenant_id)\
        .count()

    col1,col2 = st.columns(2)
    col1.metric("Revenue", f"₹ {revenue}")
    col2.metric("Orders", orders)
