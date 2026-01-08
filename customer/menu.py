import streamlit as st
from supabase_client import supabase
from datetime import datetime, timedelta

def customer_menu(tenant_name):
    st.title(f"🍽 Welcome to {tenant_name}")

    # --------------------
    # Get tenant
    # --------------------
    tenant = supabase.table("tenants") \
        .select("id") \
        .eq("name", tenant_name) \
        .execute()

    if not tenant.data:
        st.error("Restaurant not found")
        return

    tenant_id = tenant.data[0]["id"]

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
    # Get or create customer
    # --------------------
    customer = supabase.table("customers") \
        .select("*") \
        .eq("tenant_id", tenant_id) \
        .eq("mobile", mobile) \
        .execute()

    if customer.data:
        customer_id = customer.data[0]["id"]
    else:
        customer = supabase.table("customers").insert({
            "tenant_id": tenant_id,
            "name": name,
            "mobile": mobile
        }).execute()
        customer_id = customer.data[0]["id"]

    # --------------------
    # Loyalty check
    # --------------------
    discount_percent = 0
    loyalty_msg = None

    rules = supabase.table("loyalty_rules") \
        .select("*") \
        .eq("tenant_id", tenant_id) \
        .eq("active", True) \
        .execute()

    for rule in rules.data:
        since = datetime.utcnow() - timedelta(days=rule["days"])

        orders = supabase.table("orders") \
            .select("id", count="exact") \
            .eq("customer_id", customer_id) \
            .gte("created_at", since.isoformat()) \
            .execute()

        if orders.count >= rule["visits"]:
            discount_percent = rule["discount_percent"]
            loyalty_msg = (
                f"🎉 You are our loyal customer!\n\n"
                f"You placed {orders.count} orders in last {rule['days']} days.\n"
                f"As a thank you, you get **{discount_percent}% discount** on this bill."
            )
            break

    if loyalty_msg:
        st.success(loyalty_msg)

    # --------------------
    # Menu
    # --------------------
    products = supabase.table("products") \
        .select("*") \
        .eq("tenant_id", tenant_id) \
        .eq("available", True) \
        .execute()

    cart = {}
    total = 0

    st.subheader("📋 Menu")

    for p in products.data:
        cols = st.columns([1, 3, 1])
        if p.get("image_url"):
            cols[0].image(p["image_url"], width=80)

        qty = cols[2].number_input(
            f"{p['name']} – ₹{p['price']}",
            min_value=0,
            key=f"p_{p['id']}"
        )

        if qty > 0:
            cart[p["id"]] = {
                "name": p["name"],
                "qty": qty,
                "price": p["price"]
            }
            total += qty * p["price"]

    # --------------------
    # Bill
    # --------------------
    discount_amount = total * discount_percent / 100
    final_total = total - discount_amount

    st.markdown("---")
    st.write(f"Subtotal: ₹{total}")
    if discount_percent:
        st.write(f"Discount ({discount_percent}%): -₹{discount_amount}")
    st.write(f"**Total Payable: ₹{final_total}**")

    # --------------------
    # Place order
    # --------------------
    if st.button("🛒 Place Order"):
        if not cart:
            st.warning("Cart empty")
            return

        order = supabase.table("orders").insert({
            "tenant_id": tenant_id,
            "customer_id": customer_id,
            "total": final_total,
            "discount_percent": discount_percent,
            "discount_amount": discount_amount,
            "status": "open"
        }).execute()

        order_id = order.data[0]["id"]

        for item in cart.values():
            supabase.table("order_items").insert({
                "order_id": order_id,
                "product_name": item["name"],
                "quantity": item["qty"],
                "price": item["qty"] * item["price"]
            }).execute()

        st.success("✅ Order placed successfully")
        st.balloons()
