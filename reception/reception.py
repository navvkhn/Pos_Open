import streamlit as st
from supabase_client import supabase
from datetime import datetime
import pytz
import time
import math

IST = pytz.timezone("Asia/Kolkata")
time.sleep(0.2)

# --------------------------------------------------
# 🧠 TIME HELPERS (ROBUST – FIXED)
# --------------------------------------------------
def parse_utc(dt):
    if dt is None:
        return None

    if isinstance(dt, datetime):
        return dt.replace(tzinfo=None)

    if isinstance(dt, str):
        try:
            return datetime.fromisoformat(
                dt.replace("Z", "+00:00")
            ).replace(tzinfo=None)
        except Exception:
            raise ValueError(f"Invalid datetime format: {dt}")

    raise ValueError(f"Invalid datetime type: {type(dt)}")


def calculate_game_amount(game):
    """
    Pool billing with:
    - Pause support
    - 15-minute slab rounding (UP)
    """
    start = parse_utc(game["start_time"])
    now = datetime.utcnow().replace(tzinfo=None)

    if game["status"] == "paused" and game.get("paused_at"):
        now = parse_utc(game["paused_at"])

    elapsed_seconds = max(0, int((now - start).total_seconds()))
    elapsed_minutes = elapsed_seconds / 60

    # ---- 15 MIN ROUNDING ----
    billed_minutes = math.ceil(elapsed_minutes / 15) * 15 if elapsed_minutes > 0 else 0

    rate_30 = float(game["rate_per_30_min"])
    rate_per_hour = rate_30 * 2
    rate_per_15 = rate_per_hour / 4

    amount = round((billed_minutes / 15) * rate_per_15, 2)

    return elapsed_minutes, billed_minutes, rate_per_hour, amount


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
                cols = st.columns([4, 1, 1])
                cols[0].write(f"{item['product_name']} × {item['quantity']}")
                cols[1].write(f"₹{item['price']:.2f}")
                food_total += float(item["price"])

                if is_open and cols[2].button("❌", key=f"del_{item['id']}"):
                    supabase.table("order_items").delete().eq("id", item["id"]).execute()
                    st.rerun()

            if is_open and product_map:
                st.divider()
                a, b, c = st.columns([3, 1, 1])
                prod = a.selectbox("Add Item", list(product_map.keys()), key=f"p_{order_id}")
                qty = b.number_input("Qty", 1, step=1, key=f"q_{order_id}")
                if c.button("Add", key=f"add_{order_id}"):
                    supabase.table("order_items").insert({
                        "order_id": order_id,
                        "product_name": prod,
                        "quantity": qty,
                        "price": qty * product_map[prod]
                    }).execute()
                    st.rerun()

            # ---------------- POOL GAME ----------------
            st.divider()
            st.subheader("🎱 Pool Game")

            game_res = supabase.table("games") \
                .select("*") \
                .eq("order_id", order_id) \
                .order("created_at", desc=True) \
                .limit(1) \
                .execute()

            game = game_res.data[0] if game_res.data else None
            game_amount = 0.0
            pool_started = bool(game)

            if game:
                elapsed_min, billed_min, rate_hr, game_amount = calculate_game_amount(game)

                st.write(f"💲 Rate: ₹{rate_hr} / hour")
                st.write(f"⏱ Actual Time: {int(elapsed_min)} min")
                st.write(f"🧮 Billed Time (15m slabs): {billed_min} min")
                st.write(f"💰 Game Total: ₹{game_amount:.2f}")

                if is_open:
                    if game["status"] == "running":
                        if st.button("⏸ Pause Pool", key=f"pause_{game['id']}"):
                            supabase.table("games").update({
                                "status": "paused",
                                "paused_at": datetime.utcnow().isoformat()
                            }).eq("id", game["id"]).execute()
                            st.rerun()

                    elif game["status"] == "paused":
                        if st.button("▶ Resume Pool", key=f"resume_{game['id']}"):
                            supabase.table("games").update({
                                "status": "running",
                                "paused_at": None
                            }).eq("id", game["id"]).execute()
                            st.rerun()

            if not game and is_open:
                rate_hr = st.number_input(
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
                        "game_type": "pool",
                        "rate_per_30_min": rate_hr / 2,
                        "start_time": datetime.utcnow().isoformat(),
                        "status": "running"
                    }).execute()
                    st.rerun()

            # ---------------- FINAL BILL ----------------
            st.divider()
            st.subheader("🧾 Final Bill")

            grand_total = round(food_total + game_amount, 2)

            st.write(f"🍔 Food Total: ₹{food_total:.2f}")
            st.write(f"🎱 Pool Total: ₹{game_amount:.2f}")
            st.write(f"💰 **Grand Total: ₹{grand_total:.2f}**")

            if is_open and st.button("💳 Mark as Paid & Close Order", key=f"pay_{order_id}", type="primary"):
                if game:
                    supabase.table("games").update({"status": "billed"}).eq("id", game["id"]).execute()
                supabase.table("orders").update({"status": "completed"}).eq("id", order_id).execute()
                st.success("Order closed")
                st.rerun()

            # ---------------- DELETE ORDER ----------------
            if is_open and not pool_started:
                if st.button("🗑 Delete Order", key=f"delete_{order_id}"):
                    supabase.table("order_items").delete().eq("order_id", order_id).execute()
                    supabase.table("games").delete().eq("order_id", order_id).execute()
                    supabase.table("orders").delete().eq("id", order_id).execute()
                    st.success("Order deleted")
                    st.rerun()
            elif pool_started:
                st.info("🔒 Order delete disabled (pool started)")

            st.markdown("</div>", unsafe_allow_html=True)
