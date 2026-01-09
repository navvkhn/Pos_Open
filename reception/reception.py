import streamlit as st
from supabase_client import supabase
from datetime import datetime
import pytz
import time

IST = pytz.timezone("Asia/Kolkata")
time.sleep(0.2)

# --------------------------------------------------
# 🧠 HELPERS
# --------------------------------------------------
def calculate_game_amount(game):
    start = datetime.fromisoformat(game["start_time"].replace("Z", ""))
    end = datetime.utcnow()

    paused_seconds = game.get("paused_seconds", 0)

    if game["status"] == "paused" and game.get("paused_at"):
        end = datetime.fromisoformat(game["paused_at"].replace("Z", ""))

    elapsed_seconds = max(0, int((end - start).total_seconds() - paused_seconds))

    hours = elapsed_seconds // 3600
    minutes = (elapsed_seconds % 3600) // 60
    seconds = elapsed_seconds % 60

    rate = float(game["rate_per_hour"])
    amount = round((elapsed_seconds / 3600) * rate, 2)

    return elapsed_seconds, hours, minutes, seconds, amount


# --------------------------------------------------
# 🧾 RECEPTION SCREEN
# --------------------------------------------------
def reception_screen(tenant_id):
    st.title("🧾 Reception / Cashier")

    st.markdown("""
    <style>
    .order-box {
        background-color: var(--secondary-background-color);
        border: 1px solid rgba(128,128,128,0.4);
        border-radius: 12px;
        padding: 14px;
        margin-bottom: 16px;
    }
    button { min-height: 46px; font-size: 15px; }
    </style>
    """, unsafe_allow_html=True)

    if st.button("🔄 Refresh"):
        st.rerun()

    # --------------------------------------------------
    # ➕ CREATE NEW ORDER
    # --------------------------------------------------
    st.divider()
    st.subheader("➕ Create New Order")

    c1, c2 = st.columns([3, 1])

    with c1:
        new_table = st.text_input(
            "🍽 Table / Customer Name",
            placeholder="Table 5 / Walk-in / Rahul",
            key="new_table"
        )

    with c2:
        if st.button("➕ Create Order", use_container_width=True):
            supabase.table("orders").insert({
                "tenant_id": tenant_id,
                "table_name": new_table,
                "status": "open",
                "created_at": datetime.utcnow().isoformat()
            }).execute()

            st.success("Order created")
            st.rerun()

    # --------------------------------------------------
    # 📅 TODAY ORDERS
    # --------------------------------------------------
    today_ist = datetime.now(IST).replace(hour=0, minute=0, second=0, microsecond=0)
    today_utc = today_ist.astimezone(pytz.utc)

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
    # 🧾 ORDER LOOP
    # --------------------------------------------------
    for order in orders.data:
        order_id = order["id"]
        is_open = order["status"] == "open"

        with st.expander(f"🧾 Order – {order.get('table_name') or order_id}"):
            st.markdown("<div class='order-box'>", unsafe_allow_html=True)

            # ---------------- FOOD ----------------
            st.subheader("🍔 Food Items")
            food_total = 0.0

            for item in order.get("order_items", []):
                c = st.columns([4, 1, 1])
                c[0].write(f"{item['product_name']} × {item['quantity']}")
                c[1].write(f"₹{item['price']:.2f}")
                food_total += float(item["price"])

                if is_open and c[2].button("❌", key=f"del_{item['id']}"):
                    supabase.table("order_items").delete().eq("id", item["id"]).execute()
                    st.rerun()

            if is_open and product_map:
                st.divider()
                p1, p2, p3 = st.columns([3, 1, 1])
                prod = p1.selectbox("Add Item", list(product_map.keys()), key=f"p_{order_id}")
                qty = p2.number_input("Qty", 1, step=1, key=f"q_{order_id}")
                if p3.button("Add", key=f"add_{order_id}"):
                    supabase.table("order_items").insert({
                        "order_id": order_id,
                        "product_name": prod,
                        "quantity": qty,
                        "price": qty * product_map[prod]
                    }).execute()
                    st.rerun()

            # ---------------- GAME ----------------
            st.divider()
            st.subheader("🎱 Pool Game")

            game_res = supabase.table("games") \
                .select("*") \
                .eq("order_id", order_id) \
                .order("start_time", desc=True) \
                .limit(1) \
                .execute()

            game = game_res.data[0] if game_res.data else None

            if not game and is_open:
                rate = st.number_input(
                    "Pool Price (₹ / Hour)",
                    min_value=0,
                    step=50,
                    value=200,
                    key=f"rate_{order_id}"
                )

                if st.button("🎱 Start Pool", key=f"start_{order_id}"):
                    supabase.table("games").insert({
                        "tenant_id": tenant_id,
                        "order_id": order_id,
                        "rate_per_30_min": rate / 2,  # convert hour → 30 min
                        "start_time": datetime.utcnow().isoformat(),
                        "paused_seconds": 0,
                        "status": "running"
                    }).execute()
                    st.rerun()

            if game:
                elapsed, h, m, s, game_amount = calculate_game_amount(game)

                st.write(f"⏱ {h:02d}h {m:02d}m {s:02d}s")
                st.write(f"💲 Rate: ₹{game['rate_per_hour']} / hour")
                st.write(f"💰 Game Total: ₹{game_amount}")

            # ---------------- DELETE ORDER ----------------
            if is_open and st.button("🗑 Delete Order", key=f"delete_{order_id}"):
                supabase.table("order_items").delete().eq("order_id", order_id).execute()
                supabase.table("games").delete().eq("order_id", order_id).execute()
                supabase.table("orders").delete().eq("id", order_id).execute()
                st.success("Order deleted")
                st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)
