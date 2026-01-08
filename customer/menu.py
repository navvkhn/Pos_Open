import streamlit as st
from supabase_client import supabase
from datetime import datetime, timedelta
import pytz
from urllib.parse import unquote
from postgrest.exceptions import APIError

IST = pytz.timezone("Asia/Kolkata")


def customer_menu(tenant_name):
    st.set_page_config(layout="wide")

    # --------------------------------------------------
    # 🎨 MOBILE FRIENDLY CSS (SAFE)
    # --------------------------------------------------
    st.markdown("""
    <style>
    button {
        min-height: 48px;
        font-size: 16px;
    }
    input, textarea {
        font-size: 16px !important;
    }
    .block-container {
        padding-top: 1rem;
        padding-bottom: 6rem;
    }
    </style>
    """, unsafe_allow_html=True)

    # --------------------------------------------------
    # 🔎 GET TENANT (URL SAFE)
    # --------------------------------------------------
    decoded_name = unquote(tenant_name)

    try:
        tenant = supabase.table("tenants") \
            .select("*") \
            .eq("name", decoded_name) \
            .single() \
            .execute()
    except APIError:
        st.error("❌ Restaurant not found")
        return

    tenant_id = tenant.data["id"]

    # --------------------------------------------------
    # HEADER (MOBILE OPTIMIZED)
    # --------------------------------------------------
    if tenant.data.get("logo_url"):
        st.image(tenant.data["logo_url"], width=100)

    st.markdown(
        f"<h2 style='margin-bottom:0'>{tenant.data['name']}</h2>",
        unsafe_allow_html=True
    )
    st.caption("Scan • Order • Pay")

    st.divider()

    # --------------------------------------------------
    # 👤 CUSTOMER DETAILS
    # --------------------------------------------------
    st.subheader("👤 Your Details")

    col1, col2 = st.columns(2)

    with col1:
        customer_name = st.text_input("Your Name")

    with col2:
        mobile = st.text_input("Mobile Number", max_chars=10)

    if not customer_name or not mobile:
        st.info("Please enter your name and mobile number to continue")
        return

    # --------------------------------------------------
    # 👤 GET OR CREATE CUSTOMER
    # --------------------------------------------------
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
            "name": customer_name,
            "mobile": mobile
        }).execute()
        customer_id = customer.data[0]["id"]

    # --------------------------------------------------
    # ⭐ LOYALTY DISCOUNT (ONCE PER DAY)
    # --------------------------------------------------
    discount_percent = 0
    loyalty_message = None

    today_ist = datetime.now(IST).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    today_utc = today_ist.astimezone(pytz.utc)

    discount_used_today = supabase.table("orders") \
        .select("id", count="exact") \
        .eq("customer_id", customer_id) \
        .gt("discount_amount", 0) \
        .gte("created_at", today_utc.isoformat()) \
        .execute()

    if discount_used_today.count == 0:
        rules = supabase.table("loyalty_rules") \
            .select("*") \
            .eq("tenant_id", tenant_id) \
            .eq("active", True) \
            .execute()

        now_utc = datetime.utcnow()

        for rule in rules.data:
            since = now_utc - timedelta(days=rule["days"])

            visits = supabase.table("orders") \
                .select("id", count="exact") \
                .eq("customer_id", customer_id) \
                .eq("status", "completed") \
                .gte("created_at", since.isoformat()) \
                .execute()

            if visits.count >= rule["visits"]:
                discount_percent = rule["discount_percent"]
                loyalty_message = (
                    f"🎉 Loyalty Reward!\n\n"
                    f"{visits.count} visits in last {rule['days']} days.\n"
                    f"🎁 {discount_percent}% discount applied today."
                )
                break

    if loyalty_message:
        st.success(loyalty_message)

    # --------------------------------------------------
    # 📋 FETCH PRODUCTS
    # --------------------------------------------------
    try:
        products = supabase.table("products") \
            .select("*") \
            .eq("tenant_id", tenant_id) \
            .eq("available", True) \
            .order("category") \
            .execute()
    except APIError:
        st.error("⚠️ Unable to load menu. Please refresh.")
        return

    if not products.data:
        st.info("Menu coming soon!")
        return

    # --------------------------------------------------
    # 🛒 MENU (MOBILE FRIENDLY)
    # --------------------------------------------------
    st.subheader("📋 Menu")

    cart = {}
    total = 0.0

    categories = sorted(
        set(p.get("category", "Others") for p in products.data)
    )

    for category in categories:
        st.markdown(f"### 🍽 {category}")
        for p in [x for x in products.data if x.get("category") == category]:
            cols = st.columns([5, 2, 2])

            cols[0].markdown(f"**{p['name']}**")
            cols[1].markdown(f"₹{p['price']:.2f}")

            qty = cols[2].number_input(
                "Qty",
                min_value=0,
                step=1,
                key=f"qty_{p['id']}"
            )

            if qty > 0:
                cart[p["id"]] = {
                    "name": p["name"],
                    "qty": qty,
                    "price": p["price"]
                }
                total += qty * p["price"]

            st.divider()

    if not cart:
        st.info("Add items to your cart to proceed")
        return

    # --------------------------------------------------
    # 🧾 BILL SUMMARY (MOBILE STICKY FEEL)
    # --------------------------------------------------
    discount_amount = round(total * discount_percent / 100, 2)
    final_total = round(total - discount_amount, 2)

    st.subheader("🧾 Bill Summary")
    st.write(f"Subtotal: ₹{total:.2f}")

    if discount_percent:
        st.write(f"Discount ({discount_percent}%): -₹{discount_amount:.2f}")

    st.markdown(
        f"""
        <div style="padding:12px;border:1px solid #ddd;border-radius:10px">
        <h3>💰 Total Payable: ₹{final_total:.2f}</h3>
        </div>
        """,
        unsafe_allow_html=True
    )

    # --------------------------------------------------
    # 🛒 PLACE ORDER (BIG BUTTON)
    # --------------------------------------------------
    if st.button("🛒 Place Order", use_container_width=True):
        order = supabase.table("orders").insert({
            "tenant_id": tenant_id,
            "customer_id": customer_id,
            "customer_name": customer_name,
            "total": final_total,
            "discount_percent": discount_percent,
            "discount_amount": discount_amount,
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

        st.session_state["order_id"] = order_id

        st.query_params.clear()
        st.query_params["pay"] = str(order_id)
        st.rerun()
