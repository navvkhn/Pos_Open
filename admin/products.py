import streamlit as st
from db import SessionLocal
from models import Product

def products(tenant_id):
    st.title("🧾 Products")
    db = SessionLocal()

    with st.form("add"):
        name = st.text_input("Name")
        price = st.number_input("Price", min_value=0.0)
        cat = st.text_input("Category")
        if st.form_submit_button("Add"):
            db.add(Product(
                tenant_id=tenant_id,
                name=name,
                price=price,
                category=cat
            ))
            db.commit()
            st.success("Added")
            st.rerun()

    for p in db.query(Product).filter(Product.tenant_id==tenant_id):
        col1,col2,col3 = st.columns(3)
        col1.write(p.name)
        col2.write(f"₹{p.price}")
        if col3.button("❌", key=p.id):
            db.delete(p)
            db.commit()
            st.rerun()
