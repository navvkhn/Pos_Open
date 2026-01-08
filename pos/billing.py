import streamlit as st
from db import SessionLocal
from models import Product, Order, OrderItem, Discount

def billing(tenant_id):
    st.title("🧾 POS Billing")

    db = SessionLocal()

    table_no = st.text_input("Table Number")

    products = db.query(Product)\
        .filter(Product.tenant_id == tenant_id)\
        .filter(Product.available == True)\
        .all()

    cart = st.session_state.get("cart", {})

    st.subheader("Menu")
    for p in products:
        qty = st.number_input(
            f"{p.name} (₹{p.price})",
            min_value=0,
            key=f"pos_{p.id}"
        )
        if qty > 0:
            cart[p.id] = qty

    st.session_state["cart"] = cart

    st.subheader("Discount")
    discount_code = st.text_input("Discount Code")

    discount = None
    if discount_code:
        discount = db.query(Discount).filter(
            Discount.code == discount_code,
            Discount.tenant_id == tenant_id,
            Discount.active == True
        ).first()

    if st.button("Create Bill"):
        order = Order(
            tenant_id=tenant_id,
            table_no=table_no,
            total=0
        )
        db.add(order)
        db.commit()

        total = 0
        for pid, qty in cart.items():
            product = db.query(Product).get(pid)
            price = product.price * qty
            total += price
            db.add(OrderItem(
                order_id=order.id,
                product_name=product.name,
                quantity=qty,
                price=price
            ))

        if discount:
            if discount.type == "flat":
                total -= discount.value
            else:
                total -= total * (discount.value / 100)

        order.total = max(total, 0)
        db.commit()

        st.success(f"Bill Created: ₹{order.total}")
        st.session_state["cart"] = {}
        st.rerun()
