import streamlit as st
from db import SessionLocal
from models import Discount

def discounts(tenant_id):
    st.title("🏷 Discount Codes")

    db = SessionLocal()

    with st.form("add_discount"):
        code = st.text_input("Code")
        dtype = st.selectbox("Type", ["flat", "percent"])
        value = st.number_input("Value", min_value=0.0)
        submit = st.form_submit_button("Add")

        if submit:
            d = Discount(
                tenant_id=tenant_id,
                code=code,
                type=dtype,
                value=value
            )
            db.add(d)
            db.commit()
            st.success("Discount Added")
            st.rerun()

    st.subheader("Existing Discounts")
    for d in db.query(Discount).filter(Discount.tenant_id == tenant_id):
        st.write(f"{d.code} | {d.type} | {d.value}")
