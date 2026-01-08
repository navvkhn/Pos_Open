import streamlit as st
from supabase_client import supabase
from datetime import datetime, timedelta
from collections import defaultdict
import pytz

IST = pytz.timezone("Asia/Kolkata")


def customer_menu(tenant_name):
    st.set_page_config(layout="wide")
    st.title(f"🍽 Welcome to {tenant_name}")

    # --------------------------------------------------
    # FETCH TENANT
    # --------------------------------------------------
    tenant = supabase.table("tenants") \
        .select("id") \
        .eq("name", tenant_name) \
        .single() \
        .execute()

    if not tenant.data:
        st.error("Restaurant not found")
        return

    tenant_id = tenant.data["id"]

    # --------------------------------------------------
    # CUSTOMER DETAILS
    # --------------------------------------------------
    st.subheader("👤 Your Details")

    name = st.text_input("Your Name")
    mobile = st.text_input("Mobile Number")

    if not name or not mobile:
        st.info("Please enter your name and mobile number to continue")
        return

    # --------------------------------------------------
    # GET OR CREATE CUSTOMER
    # --------------------------------------------------
    customer = supabase.table("customers") \
        .select("*") \
        .eq("tenant_id", tenant_id) \
        .eq("mobile", mobile) \
        .maybe_single() \
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

    # --------------------------------------------------
    # 🔁 REPEAT LAST ORDER
    # --------------------------------------------------
    last_order = supabase.table("orders") \
        .select("id") \
        .eq("customer_id", customer_id) \
        .order("created_at", desc=True) \
        .limit(1) \
        .execute()

    if last_order.data:
        if st.button("🔁 Repeat Last Order"):
            last_items = supabase.table("order_items") \
                .select("*") \
                .eq("order_id", last_order.data[0]["id"]) \
                .execute()

            for item in last_items.data:
                st.session_state[f"p_{item['product_name']}"] = item["quantity"]

            st.success("Last order added to cart")
            st.rerun()

    st.divider()

    # --------------------------------------------------
    # ⭐ LOYALTY DISCOUNT (FIXED & WORKING)
    # --------------------------------------------------
    discount_percent = 0
    loyalty_message = None

    rules = supabase.table("loyalty_rules") \
        .select("*") \
        .eq("tenant_id", tenant_id) \
        .eq("active", True) \
        .execute()

    now_utc = datetime.utcnow()

    for rule in rules.data:
        since_utc = now_utc - timedelta(days=rule["days"])

        orders_count = supabase.table("orders") \
            .select("id", count="exact") \
            .eq("customer_id", customer_id) \
            .eq("status", "completed") \
            .gte("created_at", since_utc.isoformat()) \
            .execute()

        if orders_count.count >= rule["visits"]:
            discount_percent = rule["discount_percent"]
            loyalty_message = (
                f"🎉 You are our loyal customer!\n\n"
                f"You placed **{orders_count.count} orders** in last "
                f"**{rule['days']} days**.\n\n"
                f"🎁 You get **{discount_percent}% discount** on this bill!"
            )
            break

    if loyalty_message:
        st.success(loyalty_message)

    # --------------------------------------------------
    # 🔥 POPULAR ITEMS (OPTIONAL SUGGESTION)
    # --------------------------------------------------
    popular_items_raw = supabase.table("order_items") \
        .select("product_name, quantity") \
        .execute()

    popular_count = defaultdict(int)
    for p in popular_items_raw.data:
        popular_count[p["product_name"]] += p["quantity"]

    top_items = sorted(
        popular_count.items(),
        key=lambda x: x[1],
        reverse=True
    )[:3]

    if top_items:
        st.subheader("🔥 Popular Choices")
        for name, _ in top_items:
            st.write(f"⭐ {name}")

    st.divider()

    # --------------------------------------------------
    # FETCH PRODUCTS
    # --------------------------------------------------
    products = supabase.table("products") \
        .select("*") \
        .eq("tenant_id", tenant_id) \
        .eq("available", True) \
        .execute()

    if not products.data:
        st.info("Menu is empty")
        return

    # --------------------------------------------------
    # GROUP PRODUCTS BY CATEGORY
    # --------------------------------------------------
    grouped = defaultdict(list)
    for p in products.data:
        grouped[p.get("category", "Others")].append(p)

    cart = {}
    total = 0.0

    st.subheader("📋 Menu")

    # --------------------------------------------------
    # MENU UI (CATEGORY-WISE)
    # --------------------------------------------------
    for category, items in grouped.items():
        with st.expander(f"🍽 {category}", expanded=True):
            for p in items:
                cols = st.columns([4, 1])

                cols[0].markdown(
                    f"**{p['name']}**  \n₹{p['price']}"
                )

                qty = cols[1].number_input(
                    "Qty",
                    min_value=0,
                    step=1,
                    key=f"p_{p['name']}"
                )

                if qty > 0:
                    cart[p["id"]] = {
                        "name": p["name"],
                        "qty": qty,
                        "price": float(p["price"])
                    }
                    total += qty * float(p["price"])

    # --------------------------------------------------
    # BILL SUMMARY
    # --------------------------------------------------
    st.divider()
    st.subheader("🧾 Bill Summary")

    if not cart:
        st.info("Please add items to cart")
        return

    discount_amount = total * discount_percent / 100
    final_total = total - discount_amount

    st.write(f"Subtotal: ₹{total:.2f}")

    if discount_percent > 0:
        st.write(
            f"🎉 Loyalty Discount ({discount_percent}%): "
            f"-₹{discount_amount:.2f}"
        )

    st.write(f"**Total Payable: ₹{final_total:.2f}**")

    # --------------------------------------------------
    # PLACE ORDER
    # --------------------------------------------------
    if st.button("🛒 Place Order"):
        order = supabase.table("orders").insert({
            "tenant_id": tenant_id,
            "customer_id": customer_id,
            "customer_name": name,
            "total": float(final_total),
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

        st.success("Order placed successfully")
        st.session_state.clear()
        st.query_params.clear()
        st.query_params["pay"] = str(order_id)
        st.rerun()
