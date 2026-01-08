import streamlit as st
from supabase_client import supabase
from datetime import datetime, timedelta
import pytz
from urllib.parse import unquote
from postgrest.exceptions import APIError

IST = pytz.timezone("Asia/Kolkata")


def customer_menu(tenant_name):
    decoded_name = unquote(tenant_name)

    tenant = supabase.table("tenants") \
        .select("*") \
        .eq("name", decoded_name) \
        .single() \
        .execute()

    tenant_id = tenant.data["id"]

    if tenant.data.get("logo_url"):
        st.image(tenant.data["logo_url"], width=120)

    st.title(tenant.data["name"])
    st.divider()

    name = st.text_input("Your Name")
    mobile = st.text_input("Mobile Number", max_chars=10)

    if not name or not mobile:
        st.info("Enter details to continue")
        return

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

    # 🔢 NEXT ORDER NUMBER (PER TENANT)
    last = supabase.table("orders") \
        .select("order_number") \
        .eq("tenant_id", tenant_id) \
        .order("order_number", desc=True) \
        .limit(1) \
        .execute()

    next_order_number = (
        last.data[0]["order_number"] + 1 if last.data else 1
    )

    products = supabase.table("products") \
        .select("*") \
        .eq("tenant_id", tenant_id) \
        .eq("available", True) \
        .execute()

    cart, total = {}, 0.0

    for p in products.data:
        cols = st.columns([3, 1, 1])
        cols[0].write(p["name"])
        cols[1].write(f"₹{p['price']}")
        qty = cols[2].number_input("Qty", 0, key=f"p{p['id']}")

        if qty:
            cart[p["id"]] = (p, qty)
            total += qty * p["price"]

    if not cart:
        return

    st.divider()
    st.subheader(f"Order #{next_order_number}")
    st.write(f"Total: ₹{total:.2f}")

    if st.button("Place Order"):
        order = supabase.table("orders").insert({
            "tenant_id": tenant_id,
            "order_number": next_order_number,
            "customer_id": customer_id,
            "customer_name": name,
            "total": total,
            "status": "open",
            "payment_status": "pending"
        }).execute()

        order_id = order.data[0]["id"]

        for p, qty in cart.values():
            supabase.table("order_items").insert({
                "order_id": order_id,
                "product_name": p["name"],
                "quantity": qty,
                "price": qty * p["price"]
            }).execute()

        st.query_params.clear()
        st.query_params["pay"] = str(order_id)
        st.rerun()
