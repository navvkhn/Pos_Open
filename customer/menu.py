import streamlit as st
from supabase_client import supabase
from datetime import datetime, timedelta

def customer_menu(tenant_name):
    st.title(f"🍽 Welcome to {tenant_name}")

    tenant = supabase.table("tenants") \
        .select("id") \
        .eq("name", tenant_name) \
        .single() \
        .execute()

    if not tenant.data:
        st.error("Restaurant not found")
        return

    tenant_id = tenant.data["id"]

    # --------------------
    # Customer Info
    # --------------------
    st.subheader("👤 Your Details")
    name = st.text_input("Your Name")
    mobile = st.text_input("Mobile Number")

    if not name or not mobile:
        st.info("Please enter name and mobile to continue")
        return

    # --------------------
    # Customer lookup / create
    # --------------------
    customer = supabase.table("customers") \
        .select("id") \
        .eq("tenant_id", tenant_id) \
        .eq("mobile", mobile) \
        .single() \
        .execute()

    if customer.data:
        customer_id = customer.data["id"]
    else:
        customer = supabase.table("customers").insert({
            "tenant_id": tenant_id,
            "name": name,
            "mobile": mobile
        }).execute()
        customer_id = customer.data[0]["id"]

    # --------------------
    # Products
    # --------------------
    products = supabase.table("products") \
        .select("*") \
        .eq("tenant_id", tenant_id) \
        .eq("available", True) \
        .execute()

    if not products.data:
        st.info("Menu coming soon")
        return

    # 🔍 Search
    search = st.text_input("🔍 Search items")

    # 📂 Group by category
    categories = {}
    for p in products.data:
        if search and search.lower() not in p["name"].lower():
            continue
        categories.setdefault(p.get("category", "Others"), []).append(p)

    cart = {}
    total = 0

    st.subheader("📋 Menu")

    # 📂 Category tabs
    tabs = st.tabs(categories.keys())

    for tab, (category, items) in zip(tabs, categories.items()):
        with tab:
            for p in items:
                cols = st.columns([ 3, 1])
                
                qty = cols[2].number_input(
                    f"{p['name']} — ₹{p['price']}",
                    min_value=0,
                    step=1,
                    key=f"p_{p['id']}"
                )

                if qty > 0:
                    cart[p["id"]] = {
                        "name": p["name"],
                        "qty": qty,
                        "price": p["price"]
                    }
                    total += qty * p["price"]

    st.divider()

    if total == 0:
        st.info("Add items to cart")
        return

    st.write(f"Subtotal: ₹{total}")

    # --------------------
    # Place Order
    # --------------------
    if st.button("🛒 Place Order"):
        order = supabase.table("orders").insert({
            "tenant_id": tenant_id,
            "customer_id": customer_id,
            "customer_name": name,   # ✅ stored here
            "total": total,
            "status": "open",
            "payment_status": "pending"
        }).execute()

        order_id = order.data[0]["id"]

        for item in cart.values():
            supabase.table("order_items").insert({
                "order_id": order_id,
                "product_name": item["name"],
                "quantity": item["qty"],
                "price": item["qty"] * item["price"]
            }).execute()

        st.success("Order placed. Please proceed to payment.")
        st.query_params.clear()
        st.query_params["pay"] = str(order_id)
        st.rerun()
