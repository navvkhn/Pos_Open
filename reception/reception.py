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
    # 🎨 CSS
    # --------------------------------------------------
    st.markdown("""
    <style>
    .order-box {
        background-color: var(--secondary-background-color);
        border: 1px solid rgba(128,128,128,0.4);
        border-radius: 12px;
        padding: 14px;
        margin-bottom: 16px;
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
    # 📅 TODAY RANGE (IST → UTC)
    # --------------------------------------------------
    today_ist = datetime.now(IST).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    today_utc = today_ist.astimezone(pytz.utc)

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

    # --------------------------------------------------
    # 🎱 FETCH TODAY GAMES
    # --------------------------------------------------
    games = supabase.table("games") \
        .select("*") \
        .eq("tenant_id", tenant_id) \
        .gte("created_at", today_utc.isoformat()) \
        .execute()

    # --------------------------------------------------
    # 📦 PRODUCTS
    # --------------------------------------------------
    products = supabase.table("products") \
        .select("name, price") \
        .eq("tenant_id", tenant_id) \
        .eq("available", True) \
        .execute()

    product_map = {p["name"]: float(p["price"]) for p in products.data}

    if not orders.data:
        st.info("No orders today")
        return

    # --------------------------------------------------
    # 🧾 ORDERS LOOP
    # --------------------------------------------------
    for order in orders.data:
        order_id = order["id"]
        order_no = order.get("order_number", order_id)
        is_open = order["status"] == "open"

        with st.expander(f"🧾 Order #{order_no}"):
            st.markdown("<div class='order-box'>", unsafe_allow_html=True)

            # -----------------------------
            # 🍽 TABLE NUMBER
            # -----------------------------
            table_name = st.text_input(
                "🍽 Table Number",
                value=order.get("table_name") or "",
                disabled=not is_open,
                key=f"table_{order_id}"
            )

            # -----------------------------
            # 🍔 FOOD ITEMS
            # -----------------------------
            st.subheader("🍔 Food Items")

            food_subtotal = 0.0

            for item in order.get("order_items", []):
                cols = st.columns([4, 1, 1])
                cols[0].write(
                    f"{item['product_name']} × {item['quantity']}"
                )
                cols[1].write(f"₹{item['price']:.2f}")
                food_subtotal += float(item["price"])

                if is_open and cols[2].button("❌", key=f"del_{item['id']}"):
                    supabase.table("order_items") \
                        .delete() \
                        .eq("id", item["id"]) \
                        .execute()
                    st.rerun()

            # -----------------------------
            # ➕ ADD FOOD ITEM
            # -----------------------------
            if is_open and product_map:
                st.divider()
                col1, col2, col3 = st.columns([3, 1, 1])
                product = col1.selectbox(
                    "Add Item",
                    list(product_map.keys()),
                    key=f"prod_{order_id}"
                )
                qty = col2.number_input(
                    "Qty", 1, step=1, key=f"qty_{order_id}"
                )
                if col3.button("Add", key=f"add_{order_id}"):
                    supabase.table("order_items").insert({
                        "order_id": order_id,
                        "product_name": product,
                        "quantity": qty,
                        "price": qty * product_map[product]
                    }).execute()
                    st.rerun()

            # -----------------------------
            # 🎱 GAME BILL (COMBINED)
            # -----------------------------
            st.divider()
            st.subheader("🎱 Pool Game")

            game = next(
                (g for g in games.data if g.get("status") in ["running", "paused", "stopped"]),
                None
            )

            game_amount = 0.0

            if game:
                game_amount = float(game.get("total_amount") or 0)
                st.write(
                    f"Duration: {game.get('total_minutes', 0)} mins"
                )
                st.write(
                    f"Game Amount: ₹{game_amount:.2f}"
                )
            else:
                st.info("No pool game linked")

            # -----------------------------
            # 🧮 COMBINED BILL
            # -----------------------------
            combined_subtotal = food_subtotal + game_amount

            discount_percent = st.number_input(
                "Discount %",
                0.0, 100.0,
                value=float(order.get("discount_percent") or 0),
                step=1.0,
                disabled=not is_open,
                key=f"dp_{order_id}"
            )

            discount_amount = round(
                combined_subtotal * discount_percent / 100, 2
            )

            final_total = round(
                combined_subtotal - discount_amount, 2
            )

            st.markdown(
                f"""
                **Food:** ₹{food_subtotal:.2f}  
                **Game:** ₹{game_amount:.2f}  
                **Subtotal:** ₹{combined_subtotal:.2f}  
                **Discount:** ₹{discount_amount:.2f}  
                **Total:** ₹{final_total:.2f}
                """
            )

            # -----------------------------
            # 💾 SAVE BILL
            # -----------------------------
            if is_open and st.button("💾 Save Bill", use_container_width=True):
                supabase.table("orders").update({
                    "table_name": table_name,
                    "discount_percent": discount_percent,
                    "discount_amount": discount_amount,
                    "total": final_total
                }).eq("id", order_id).execute()

                if game:
                    supabase.table("games").update({
                        "status": "billed"
                    }).eq("id", game["id"]).execute()

                st.success("Bill saved")
                st.rerun()

            # -----------------------------
            # 🚫 CLOSE ORDER
            # -----------------------------
            if is_open and st.button("🚫 Close Order", use_container_width=True):
                supabase.table("orders") \
                    .update({"status": "completed"}) \
                    .eq("id", order_id) \
                    .execute()
                st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)
