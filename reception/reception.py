import streamlit as st
from supabase_client import supabase
from datetime import datetime
import pytz
import time

IST = pytz.timezone("Asia/Kolkata")
time.sleep(0.2)

# --------------------------------------------------
# 🧠 TIME HELPERS
# --------------------------------------------------
def parse_utc(dt):
    if isinstance(dt, str):
        return datetime.fromisoformat(dt.replace("Z", "")).replace(tzinfo=None)
    return dt.replace(tzinfo=None)


def calculate_game_amount(game):
    start = parse_utc(game["start_time"])
    now = datetime.utcnow().replace(tzinfo=None)

    if game["status"] == "paused" and game.get("paused_at"):
        now = parse_utc(game["paused_at"])

    elapsed_seconds = max(0, int((now - start).total_seconds()))

    rate_30 = float(game["rate_per_30_min"])
    rate_per_hour = rate_30 * 2
    amount = round((elapsed_seconds / 3600) * rate_per_hour, 2)

    return elapsed_seconds, rate_per_hour, amount


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

            # ---------------- GAME ----------------
            st.subheader("🎱 Pool Game")

            game_res = supabase.table("games") \
                .select("*") \
                .eq("order_id", order_id) \
                .order("created_at", desc=True) \
                .limit(1) \
                .execute()

            game = game_res.data[0] if game_res.data else None
            game_amount = 0.0

            if game:
                _, rate_hr, game_amount = calculate_game_amount(game)
                st.write(f"💲 Rate: ₹{rate_hr} / hour")
                st.write(f"💰 Game Total: ₹{game_amount}")

                # ▶⏸ PAUSE / RESUME CONTROLS (NEW)
                if is_open:
                    if game["status"] == "running":
                        if st.button("⏸ Pause Pool", key=f"pause_{game['id']}"):
                            supabase.table("games").update({
                                "status": "paused",
                                "paused_at": datetime.utcnow().isoformat()
                            }).eq("id", game["id"]).execute()
                            st.success("Pool paused")
                            st.rerun()

                    elif game["status"] == "paused":
                        if st.button("▶ Resume Pool", key=f"resume_{game['id']}"):
                            supabase.table("games").update({
                                "status": "running",
                                "paused_at": None
                            }).eq("id", game["id"]).execute()
                            st.success("Pool resumed")
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

            st.markdown("</div>", unsafe_allow_html=True)
