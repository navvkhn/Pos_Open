import streamlit as st
from supabase_client import supabase
from datetime import datetime
import pytz
from urllib.parse import unquote

IST = pytz.timezone("Asia/Kolkata")

# --------------------------------------------------
# 🧠 HELPERS
# --------------------------------------------------
def safe_int(val, default=0):
    try:
        return int(val)
    except Exception:
        return default


def customer_menu(tenant_name):
    decoded_name = unquote(tenant_name)

    # --------------------------------------------------
    # 🏪 FETCH TENANT (SAFE)
    # --------------------------------------------------
    tenant = supabase.table("tenants") \
        .select("*") \
        .eq("name", decoded_name) \
        .limit(1) \
        .execute()

    if not tenant.data:
        st.error("Invalid restaurant")
        return

    tenant = tenant.data[0]
    tenant_id = tenant["id"]

    if tenant.get("logo_url"):
        st.image(tenant["logo_url"], width=120)

    st.title(tenant["name"])
    st.divider()

    # --------------------------------------------------
    # 👤 CUSTOMER DETAILS
    # --------------------------------------------------
    name = st.text_input("Your Name", key="cust_name")

    def on_mobile_change():
        mobile = st.session_state.get("cust_mobile", "")
        if len(mobile) == 10 and mobile.isdigit():
            st.session_state["mobile_ready"] = True

    mobile = st.text_input(
        "Mobile Number",
        max_chars=10,
        key="cust_mobile",
        on_change=on_mobile_change
    )

    if not name or not mobile or len(mobile) < 10:
        st.info("Enter name and 10-digit mobile number")
        return

    # --------------------------------------------------
    # 👥 CUSTOMER LOOKUP / CREATE
    # --------------------------------------------------
    customer = supabase.table("customers") \
        .select("*") \
        .eq("tenant_id", tenant_id) \
        .eq("mobile", mobile) \
        .limit(1) \
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

    # --------------------------------------------------
    # 🔢 NEXT ORDER NUMBER (SAFE)
    # --------------------------------------------------
    last = supabase.table("orders") \
        .select("order_number") \
        .eq("tenant_id", tenant_id) \
        .order("order_number", desc=True) \
        .limit(1) \
        .execute()

    last_no = safe_int(last.data[0]["order_number"]) if last.data else 0
    next_order_number = last_no + 1

    # --------------------------------------------------
    # 🍽 PRODUCTS
    # --------------------------------------------------
    products = supabase.table("products") \
        .select("*") \
        .eq("tenant_id", tenant_id) \
        .eq("available", True) \
        .execute()

    cart = {}
    total = 0.0

    for p in products.data:
        cols = st.columns([3, 1, 1])
        cols[0].write(p["name"])
        cols[1].write(f"₹{p['price']}")
        qty = cols[2].number_input(
            "Qty",
            0,
            step=1,
            key=f"p{p['id']}"
        )

        if qty:
            cart[p["id"]] = (p, qty)
            total += qty * float(p["price"])

    if not cart:
        return

    # --------------------------------------------------
    # 🧾 ORDER SUMMARY
    # --------------------------------------------------
    st.divider()
    st.subheader(f"Order #{next_order_number}")
    st.write(f"Total: ₹{total:.2f}")

    # --------------------------------------------------
    # 📦 PLACE ORDER
    # --------------------------------------------------
    if st.button("Place Order", use_container_width=True):
        order = supabase.table("orders").insert({
            "tenant_id": tenant_id,
            "order_number": next_order_number,
            "customer_id": customer_id,
            "customer_name": name,
            "total": total,
            "status": "open",
            "payment_status": "pending",
            "created_at": datetime.utcnow().isoformat()
        }).execute()

        order_id = order.data[0]["id"]

        for p, qty in cart.values():
            supabase.table("order_items").insert({
                "order_id": order_id,
                "product_name": p["name"],
                "quantity": qty,
                "price": qty * float(p["price"])
            }).execute()

        st.success("✅ Order placed successfully")
        st.query_params.clear()
        st.query_params["pay"] = str(order_id)
        st.rerun()
