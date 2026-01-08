import streamlit as st
from db import SessionLocal
from models import Product, Order, OrderItem

def customer_menu(tenant_id):
    st.title("📱 Customer Menu")

    db = SessionLocal()

    table_no = st.text_input("Your Table Number")

    products = db.query(Product)\
        .filter(Product.tenant_id == tenant_id)\
        .filter(Product.available == True)\
        .all()

    cart = st.session_state.get("cust_cart", {})

    st.subheader("Menu")
    for p in products:
        qty = st.number_input(
            f"{p.name} (₹{p.price})",
            min_value=0,
            key=f"cust_{p.id}"
        )
        if qty > 0:
            cart[p.id] = qty

    st.session_state["cust_cart"] = cart

    if st.button("Place Order"):
        if not cart:
            st.warning("Cart is empty")
            return

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

        order.total = total
        db.commit()

        st.success("✅ Order placed successfully!")
        st.session_state["cust_cart"] = {}
        st.rerun()
