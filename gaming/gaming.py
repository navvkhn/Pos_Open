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

# ---------------- CSS ----------------
st.markdown("""
<style>
body {
    text-align: center;
}
.live-card {
    max-width: 420px;
    margin: auto;
    padding: 22px;
    border-radius: 18px;
    background-color: var(--secondary-background-color);
    border: 1px solid rgba(255,255,255,0.15);
}
.live-title {
    font-size: 28px;
    font-weight: 700;
    margin-bottom: 8px;
}
.live-sub {
    font-size: 18px;
    opacity: 0.85;
    margin-bottom: 16px;
}
.live-label {
    font-size: 14px;
    opacity: 0.7;
    margin-top: 14px;
}
.live-value {
    font-size: 22px;
    font-weight: 600;
}
.timer {
    font-family: monospace;
    font-size: 26px;
    font-weight: 700;
    letter-spacing: 1px;
}
</style>
""", unsafe_allow_html=True)

# ---------------- TITLE ----------------
st.markdown("<div class='live-title'>🎱 Pool Table Live</div>", unsafe_allow_html=True)

# ---------------- HELPERS ----------------
def parse_utc(dt):
    if isinstance(dt, str):
        return datetime.fromisoformat(dt.replace("Z", "")).replace(tzinfo=None)
    return dt.replace(tzinfo=None)

# ---------------- HARD REFRESH (2 MIN) ----------------
if "last_hard_refresh" not in st.session_state:
    st.session_state.last_hard_refresh = datetime.utcnow()

if datetime.utcnow() - st.session_state.last_hard_refresh > timedelta(minutes=2):
    st.session_state.last_hard_refresh = datetime.utcnow()
    st.rerun()

# ---------------- FETCH RUNNING GAME ----------------
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
    st.markdown("<div class='live-sub'>No active pool game</div>", unsafe_allow_html=True)
    time.sleep(2)
    st.rerun()

game = game_res.data[0]

# ---------------- FETCH CUSTOMER NAME ----------------
customer = "—"
try:
    order = supabase.table("orders") \
        .select("table_name") \
        .eq("id", game["order_id"]) \
        .single() \
        .execute()
    customer = order.data.get("table_name") or "—"
except Exception:
    pass

# ---------------- TIME CALC ----------------
start = parse_utc(game["start_time"])
now = datetime.utcnow().replace(tzinfo=None)

elapsed_seconds = max(0, int((now - start).total_seconds()))
h = elapsed_seconds // 3600
m = (elapsed_seconds % 3600) // 60
s = elapsed_seconds % 60

elapsed_str = f"{h:02d}:{m:02d}:{s:02d}"

# ---------------- AMOUNT ----------------
rate_30 = float(game.get("rate_per_30_min", 0))
rate_hr = rate_30 * 2
amount = round((elapsed_seconds / 3600) * rate_hr, 2)

# ---------------- RENDER CARD (IMPORTANT) ----------------
st.markdown(f"""
<div class="live-card">
    <div class="live-sub">👤 {customer}</div>

    <div class="live-label">🎱 Price / Hour</div>
    <div class="live-value">₹ {rate_hr}</div>

    <div class="live-label">🕒 Started At</div>
    <div class="live-value">{start.astimezone(IST).strftime("%I:%M:%S %p")}</div>

    <div class="live-label">⏱ Time Elapsed</div>
    <div class="timer">{elapsed_str}</div>

    <div class="live-label">💰 Total Spend</div>
    <div class="live-value">₹ {amount}</div>
</div>
""", unsafe_allow_html=True)

st.caption("Live • Auto-updating")

# ---------------- SOFT CLOCK TICK ----------------
time.sleep(1)
st.rerun()
