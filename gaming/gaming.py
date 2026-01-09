import streamlit as st
from supabase_client import supabase
from datetime import datetime, timedelta
import pytz
import time

IST = pytz.timezone("Asia/Kolkata")

st.set_page_config(
    page_title="Pool Table Live",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.title("🎱 Pool Table Live")

# --------------------------------------------------
# 🧠 TIME PARSER (SAFE)
# --------------------------------------------------
def parse_utc(dt):
    if isinstance(dt, str):
        return datetime.fromisoformat(dt.replace("Z", ""))
    return dt

# --------------------------------------------------
# 🔁 HARD REFRESH EVERY 2 MINUTES
# --------------------------------------------------
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = datetime.utcnow()

if datetime.utcnow() - st.session_state.last_refresh >= timedelta(minutes=2):
    st.session_state.last_refresh = datetime.utcnow()
    st.rerun()

# --------------------------------------------------
# 🎱 FETCH RUNNING GAME
# --------------------------------------------------
try:
    game_res = supabase.table("games") \
        .select("*") \
        .eq("status", "running") \
        .order("created_at", desc=True) \
        .limit(1) \
        .execute()
except Exception:
    st.error("Unable to load gaming screen")
    time.sleep(5)
    st.rerun()

if not game_res.data:
    st.info("No active pool game")
    time.sleep(10)
    st.rerun()

game = game_res.data[0]

# --------------------------------------------------
# 👤 FETCH CUSTOMER NAME
# --------------------------------------------------
order = supabase.table("orders") \
    .select("table_name") \
    .eq("id", game["order_id"]) \
    .single() \
    .execute()

customer_name = order.data.get("table_name") or "—"

# --------------------------------------------------
# ⏱ TIME CALCULATION (STATIC PER REFRESH)
# --------------------------------------------------
start_time = parse_utc(game["start_time"])
now = datetime.utcnow()

elapsed_seconds = max(0, int((now - start_time).total_seconds()))

hours = elapsed_seconds // 3600
minutes = (elapsed_seconds % 3600) // 60

elapsed_str = f"{hours:02d}:{minutes:02d}"

# --------------------------------------------------
# 💰 AMOUNT CALCULATION
# --------------------------------------------------
rate_30 = float(game.get("rate_per_30_min", 0))
rate_per_hour = rate_30 * 2

amount = round((elapsed_seconds / 3600) * rate_per_hour, 2)

# --------------------------------------------------
# 📺 CENTERED DISPLAY (PURE STREAMLIT)
# --------------------------------------------------
left, center, right = st.columns([1, 2, 1])

with center:
    st.subheader(f"👤 {customer_name}")

    st.write("🎱 **Price / Hour**")
    st.write(f"₹ {rate_per_hour}")

    st.write("🕒 **Started At**")
    st.write(start_time.astimezone(IST).strftime("%I:%M %p"))

    st.write("⏱ **Time Elapsed**")
    st.write(elapsed_str)

    st.write("💰 **Total Spend**")
    st.write(f"₹ {amount}")

st.caption("Auto-refresh every 2 minutes")
