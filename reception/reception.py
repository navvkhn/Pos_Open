import streamlit as st
from supabase_client import supabase
from datetime import datetime
import pytz
import time

IST = pytz.timezone("Asia/Kolkata")
time.sleep(0.3)

# --------------------------------------------------
# 🧠 HELPERS
# --------------------------------------------------
def calculate_game_amount(game):
    if not game or not game.get("start_time"):
        return 0, 0

    start = datetime.fromisoformat(game["start_time"].replace("Z", ""))
    end = datetime.utcnow()

    paused_seconds = game.get("paused_seconds", 0)

    if game["status"] == "paused" and game.get("paused_at"):
        paused_at = datetime.fromisoformat(game["paused_at"].replace("Z", ""))
        end = paused_at

    elapsed_seconds = (end - start).total_seconds() - paused_seconds
    minutes = max(0, int(elapsed_seconds / 60))

    rate = float(game.get("rate_per_30_min", 0))
    amount = round((minutes / 30) * rate, 2)

    return minutes, amount


# --------------------------------------------------
# 🧾 RECEPTION SCREEN
# --------------------------------------------------
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
    button { min-height: 48px; font-size: 16px; }
    </style>
    """, unsafe_allow_html=True)

    if st.button("🔄 Refresh"):
        st.rerun()

    # --------------------------------------------------
    # ➕ CREATE NEW ORDER (ONLY META + GAME RATE)
    # --------------------------------------------------
    st.divider()
    st.subheader("➕ Create New Order")

    c1, c2, c3 = st.columns([2, 1, 1])

    with c1:
        new_table_name = st.text_input(
            "🍽 Table / Customer Name",
            placeholder="Table 5 / Walk-in / Rahul",
            key="new_order_table"
        )

    with c2:
        default_game_rate = st.number_input(
            "🎱 Pool Rate (₹ / 30 min)",
            min_value=0,
            step=50,
            value=100,
            key="default_game_rate"
        )

    with c3:
        if st.button("➕ Create Order", use_container_width=True, key="create_order"):
            supabase.table("orders").insert({
                "tenant_id": tenant_id,
                "table_name": new_table_name,
                "status": "open",
                "has_game": False,
                "created_at": datetime.utcnow().isoformat()
            }).execute()

            st.session_state["last_game_rate"] = default_game_rate
            st.success("✅ Order created")
            st.rerun()

    # --------------------------------------------------
    # 📅 TODAY RANGE
    # --------------------------------------------------
    today_ist = datetime.now(IST).replace(hour=0, minute=0, second=0, microsecond=0)
    today_utc = today_ist.astimezone(pytz.utc)

    # --------------------------------------------------
    # 📦 DATA FETCH
    # --------------------------------------------------
    orders = supabase.table("orders") \
        .select("*, order_items(*)") \
        .eq("tenant_id", tenant_id) \
        .gte("created_at", today_utc.isoformat()) \
        .order("created_at", desc=True) \
        .execute()

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
        is_open = order["status"] == "open"

        with st.expander(f"🧾 Order #{order.get('order_number', order_id)}"):
            st.markdown("<div class='order-box'>", unsafe_allow_html=True)

            table_name = st.text_input(
                "🍽 Table Number",
                value=order.get("table_name") or "",
                disabled=not is_open,
                key=f"table_{order_id}"
            )

            # ---------------- FOOD (SAME AS CUSTOMER MENU) ---------------- #
            st.subheader("🍔 Food Items")
            food_total = 0.0

            for item in order.get("order_items", []):
                cols = st.columns([4, 1, 1])
                cols[0].write(f"{item['product_name']} × {item['quantity']}")
                cols[1].write(f"₹{item['price']:.2f}")
                food_total += float(item["price"])

                if is_open and cols[2].button("❌", key=f"del_{item['id']}"):
                    supabase.table("order_items") \
                        .delete() \
                        .eq("id", item["id"]) \
                        .execute()
                    st.rerun()

            if is_open and product_map:
                st.divider()
                c1, c2, c3 = st.columns([3, 1, 1])
                prod = c1.selectbox("Add Item", list(product_map.keys()), key=f"p_{order_id}")
                qty = c2.number_input("Qty", 1, step=1, key=f"q_{order_id}")
                if c3.button("Add", key=f"add_{order_id}"):
                    supabase.table("order_items").insert({
                        "order_id": order_id,
                        "product_name": prod,
                        "quantity": qty,
                        "price": qty * product_map[prod]
                    }).execute()
                    st.rerun()

            # ---------------- GAME (ONLY ADDITION) ---------------- #
            st.divider()
            st.subheader("🎱 Pool Game")

            game_res = supabase.table("games") \
                .select("*") \
                .eq("order_id", order_id) \
                .order("created_at", desc=True) \
                .limit(1) \
                .execute()

            game = game_res.data[0] if game_res.data else None

            if not game and is_open:
                rate = st.session_state.get("last_game_rate", 100)

                if st.button("🎱 Start Pool Game", key=f"start_{order_id}"):
                    supabase.table("games").insert({
                        "tenant_id": tenant_id,
                        "order_id": order_id,
                        "game_type": "pool",
                        "rate_per_30_min": rate,
                        "start_time": datetime.utcnow().isoformat(),
                        "paused_seconds": 0,
                        "status": "running"
                    }).execute()

                    supabase.table("orders") \
                        .update({"has_game": True}) \
                        .eq("id", order_id) \
                        .execute()

                    st.rerun()

            if game:
                minutes, game_amount = calculate_game_amount(game)

                st.write(f"⏱ {minutes} mins")
                st.write(f"💲 Rate: ₹{game['rate_per_30_min']} / 30 min")
                st.write(f"💰 Game Amount: ₹{game_amount}")

                if game["status"] == "running" and st.button("⏸ Pause Game", key=f"pause_{order_id}"):
                    supabase.table("games").update({
                        "status": "paused",
                        "paused_at": datetime.utcnow().isoformat()
                    }).eq("id", game["id"]).execute()
                    st.rerun()

                if game["status"] == "paused" and st.button("▶ Resume Game", key=f"resume_{order_id}"):
                    paused_at = datetime.fromisoformat(game["paused_at"].replace("Z", ""))
                    paused_secs = (datetime.utcnow() - paused_at).total_seconds()

                    supabase.table("games").update({
                        "status": "running",
                        "paused_at": None,
                        "paused_seconds": game.get("paused_seconds", 0) + paused_secs
                    }).eq("id", game["id"]).execute()
                    st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)
