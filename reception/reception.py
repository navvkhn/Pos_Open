import streamlit as st
from supabase_client import supabase
from datetime import datetime
import pytz
import time

IST = pytz.timezone("Asia/Kolkata")
time.sleep(0.3)


def reception_screen(tenant_id):
    st.title("🧾 Reception / Cashier")

    # --------------------------------------------------
    # 🎨 MOBILE SAFE CSS
    # --------------------------------------------------
    st.markdown("""
    <style>
    .order-box {
        background-color: var(--secondary-background-color);
        border: 1px solid rgba(128,128,128,0.4);
        border-radius: 12px;
        padding: 12px;
        margin-bottom: 14px;
    }
    button {
        min-height: 48px;
        font-size: 16px;
    }
    </style>
    """, unsafe_allow_html=True)

    if st.button("🔄 Refresh"):
        st.rerun()

    # --------------------------------------------------
    # 📅 TODAY RANGE
    # --------------------------------------------------
    today_ist = datetime.now(IST).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    today_utc = today_ist.astimezone(pytz.utc)

    # --------------------------------------------------
    # 📊 METRICS
    # --------------------------------------------------
    unpaid = supabase.table("orders") \
        .select("id", count="exact") \
        .eq("tenant_id", tenant_id) \
        .eq("payment_status", "pending") \
        .gte("created_at", today_utc.isoformat()) \
        .execute()

    open_orders = supabase.table("orders") \
        .select("id", count="exact") \
        .eq("tenant_id", tenant_id) \
        .eq("status", "open") \
        .gte("created_at", today_utc.isoformat()) \
        .execute()

    c1, c2 = st.columns(2)
    c1.metric("💳 Unpaid", unpaid.count)
    c2.metric("🕒 Open Orders", open_orders.count)

    st.divider()

    # --------------------------------------------------
    # 🧾 FETCH TODAY ORDERS
    # --------------------------------------------------
    orders = supabase.table("orders") \
        .select("""
            *,
            order_items (
                id,
                product_name,
                quantity,
                price
            )
        """) \
        .eq("tenant_id", tenant_id) \
        .gte("created_at", today_utc.isoformat()) \
        .order("created_at", desc=True) \
        .execute()

    if not orders.data:
        st.info("No orders today")
        return

    # --------------------------------------------------
    # 📦 FETCH PRODUCTS (ONCE)
    # --------------------------------------------------
    products = supabase.table("products") \
        .select("name, price") \
        .eq("tenant_id", tenant_id) \
        .eq("available", True) \
        .order("name") \
        .execute()

    product_map = {
        p["name"]: float(p["price"])
        for p in products.data
    }

    # --------------------------------------------------
    # 🧾 ORDERS LOOP
    # --------------------------------------------------
    for order in orders.data:
        order_id = order["id"]
        order_no = order.get("order_number", "—")
        is_open = order.get("status") == "open"
        total = float(order.get("total") or 0)

        header = f"Order #{order_no} | ₹{total:.2f}"

        with st.expander(header):
            st.markdown("<div class='order-box'>", unsafe_allow_html=True)

            # --------------------------------------------------
            # 🧾 EXISTING ITEMS
            # --------------------------------------------------
            st.subheader("🧾 Items")

            items_total = 0.0

            for item in order.get("order_items", []):
                cols = st.columns([4, 1, 1])

                cols[0].write(
                    f"{item['product_name']} × {item['quantity']}"
                )

                cols[1].write(f"₹{item['price']:.2f}")
                items_total += float(item["price"])

                if is_open:
                    if cols[2].button("❌", key=f"del_{item['id']}"):
                        supabase.table("order_items") \
                            .delete() \
                            .eq("id", item["id"]) \
                            .execute()
                        st.rerun()

            # --------------------------------------------------
            # ➕ ADD NEW ITEM
            # --------------------------------------------------
            if is_open and product_map:
                st.divider()
                st.subheader("➕ Add Item")

                col1, col2, col3 = st.columns([3, 1, 1])

                product_name = col1.selectbox(
                    "Product",
                    options=list(product_map.keys()),
                    key=f"prod_{order_id}"
                )

                qty = col2.number_input(
                    "Qty",
                    min_value=1,
                    step=1,
                    key=f"qty_{order_id}"
                )

                if col3.button("Add", key=f"add_{order_id}"):
                    price = product_map[product_name] * qty

                    supabase.table("order_items").insert({
                        "order_id": order_id,
                        "product_name": product_name,
                        "quantity": qty,
                        "price": price
                    }).execute()

                    # 🔁 Update order total
                    new_total = items_total + price

                    supabase.table("orders") \
                        .update({"total": new_total}) \
                        .eq("id", order_id) \
                        .execute()

                    st.rerun()

            # --------------------------------------------------
            # 💰 TOTAL (LIVE)
            # --------------------------------------------------
            st.divider()
            st.markdown(f"### 💰 Total: ₹{items_total:.2f}")

            # --------------------------------------------------
            # CLOSE ORDER
            # --------------------------------------------------
            if is_open:
                if st.button("🚫 Close Order", key=f"close_{order_id}", use_container_width=True):
                    supabase.table("orders") \
                        .update({"status": "completed"}) \
                        .eq("id", order_id) \
                        .execute()
                    st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)
