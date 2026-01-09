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

# --------------------------------------------------
# 🎨 SIMPLE CSS (CENTERED, STABLE)
# --------------------------------------------------
st.markdown("""
<style>
body {
    text-align: center;
}
.card {
    max-width: 420px;
    margin: auto;
    padding: 22px;
    border-radius: 16px;
    background-color: var(--secondary-background-color);
    border: 1px solid rgba(255,255,255,0.15);
}
.title {
    font-size: 26px;
    font-weight: 700;
    margin-bottom: 12px;
}
.label {
    font-size: 14px;
    opacity: 0.7;
    margin-top: 14px;
}
.value {
    font-size: 22px;
    font-weight: 600;
}
.timer {
    font-family: monospace;
    font-size: 24px;
    font-weight: 700;
}
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='title'>🎱 Pool Table Live</div>", unsafe_allow_html=True)

# --------------------------------------------------
# 🧠 TIME HELPERS
# --------------------------------------------------
def parse_utc(dt):
    if isinstance(dt, str):
        return datetime.fromisoformat(dt.replace("Z", "")).replace(tzinfo=None)
    return dt.replace(tzinfo=None)

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
game_res = supabase.table("games") \
    .select("*") \
    .eq("status", "running") \
    .order("created_at", desc=True) \
    .limit(1) \
    .execute()

if not game_res.data:
    st.markdown("<div class='card'><div class='value'>No active pool game</div></div>", unsafe_allow_html=True)
    time.sleep(10)
    st.rerun()

game = game_res.data[0]

# --------------------------------------------------
# 👤 FETCH CUSTOMER NAME
# --------------------------------------------------
customer = "—"
order = supabase.table("orders") \
    .select("table_name") \
    .eq("id", game["order_id"]) \
    .single() \
    .execute()

customer = order.data.get("table_name") or "—"

# --------------------------------------------------
# ⏱ TIME CALCULATION (STATIC PER REFRESH)
# --------------------------------------------------
start_time = parse_utc(game["start_time"])
now = datetime.utcnow().replace(tzinfo=None)

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
# 📺 DISPLAY CARD
# --------------------------------------------------
st.markdown(f"""
<div class="card">
    <div class="value">👤 {customer}</div>

    <div class="label">🎱 Price / Hour</div>
    <div class="value">₹ {rate_per_hour}</div>

    <div class="label">🕒 Started At</div>
    <div class="value">
        {start_time.astimezone(IST).strftime("%I:%M %p")}
    </div>

    <div class="label">⏱ Time Elapsed</div>
    <div class="timer">{elapsed_str}</div>

    <div class="label">💰 Total Spend</div>
    <div class="value">₹ {amount}</div>
</div>
""", unsafe_allow_html=True)

st.caption("Auto-refresh every 2 minutes")
