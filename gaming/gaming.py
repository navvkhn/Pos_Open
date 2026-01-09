import streamlit as st
from supabase_client import supabase
from datetime import datetime, timedelta
import pytz
import time

IST = pytz.timezone("Asia/Kolkata")

st.set_page_config(layout="centered")
st.title("🎱 Pool Table Live")

# --------------------------------------------------
# 🧠 TIME HELPERS (SAFE)
# --------------------------------------------------
def parse_utc(dt):
    if isinstance(dt, str):
        return datetime.fromisoformat(dt.replace("Z", "")).replace(tzinfo=None)
    if isinstance(dt, datetime):
        return dt.replace(tzinfo=None)
    return None


# --------------------------------------------------
# 🔁 HARD AUTO REFRESH (EVERY 2 MINUTES)
# --------------------------------------------------
if "last_hard_refresh" not in st.session_state:
    st.session_state.last_hard_refresh = datetime.utcnow()

if datetime.utcnow() - st.session_state.last_hard_refresh > timedelta(minutes=2):
    st.session_state.last_hard_refresh = datetime.utcnow()
    st.rerun()

# --------------------------------------------------
# 🎱 FETCH RUNNING GAME (SAFE)
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
    time.sleep(2)
    st.rerun()

if not game_res.data:
    st.info("No active pool game")
    time.sleep(2)
    st.rerun()

game = game_res.data[0]

# --------------------------------------------------
# 🧾 FETCH ORDER (CUSTOMER NAME)
# --------------------------------------------------
order_name = "—"

try:
    order_res = supabase.table("orders") \
        .select("table_name") \
        .eq("id", game["order_id"]) \
        .single() \
        .execute()

    order_name = order_res.data.get("table_name") or "—"
except Exception:
    pass

# --------------------------------------------------
# ⏱ TIME CALCULATION (CONTINUOUS)
# --------------------------------------------------
start_time = parse_utc(game.get("start_time"))
now = datetime.utcnow().replace(tzinfo=None)

if not start_time:
    st.error("Invalid game start time")
    time.sleep(2)
    st.rerun()

elapsed_seconds = max(0, int((now - start_time).total_seconds()))

hours = elapsed_seconds // 3600
minutes = (elapsed_seconds % 3600) // 60
seconds = elapsed_seconds % 60

elapsed_str = f"{hours:02d} hrs {minutes:02d} Mins {seconds:02d} Sec"

# --------------------------------------------------
# 💰 AMOUNT CALCULATION
# --------------------------------------------------
rate_30 = float(game.get("rate_per_30_min", 0))
rate_per_hour = rate_30 * 2

amount = round((elapsed_seconds / 3600) * rate_per_hour, 2)

# --------------------------------------------------
# 📺 DISPLAY
# --------------------------------------------------
st.subheader(f"👤 {order_name}")

st.metric("🎱 Pool Price", f"₹ {rate_per_hour} / Hour")
st.metric(
    "🕒 Started At",
    start_time.astimezone(IST).strftime("%I:%M:%S %p")
)
st.metric("⏱ Time Elapsed", elapsed_str)
st.metric("💰 Total Spend", f"₹ {amount}")

st.caption("Auto-updating live")

# --------------------------------------------------
# ⏲ SOFT REFRESH (EVERY SECOND – CLOCK ONLY)
# --------------------------------------------------
time.sleep(1)
st.rerun()
