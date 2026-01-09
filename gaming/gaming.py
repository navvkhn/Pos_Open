import streamlit as st
from supabase_client import supabase
from datetime import datetime, timedelta
import pytz
import time

IST = pytz.timezone("Asia/Kolkata")

st.set_page_config(layout="centered")
st.title("🎱 Pool Table Live")

# -------------------------------
# Auto refresh every 2 minutes
# -------------------------------
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = datetime.utcnow()

if datetime.utcnow() - st.session_state.last_refresh > timedelta(minutes=2):
    st.session_state.last_refresh = datetime.utcnow()
    st.rerun()

# -------------------------------
# Fetch running game
# -------------------------------
game_res = supabase.table("games") \
    .select("*, orders(table_name)") \
    .eq("status", "running") \
    .order("start_time", desc=True) \
    .limit(1) \
    .execute()

if not game_res.data:
    st.warning("No active pool game")
    time.sleep(2)
    st.rerun()

game = game_res.data[0]

# -------------------------------
# Time calculations
# -------------------------------
start_utc = datetime.fromisoformat(game["start_time"].replace("Z", ""))
now_utc = datetime.utcnow()

elapsed_seconds = int(
    (now_utc - start_utc).total_seconds()
    - game.get("paused_seconds", 0)
)

hours = elapsed_seconds // 3600
minutes = (elapsed_seconds % 3600) // 60
seconds = elapsed_seconds % 60

elapsed_str = f"{hours:02d} Hours {minutes:02d} Minutes {seconds:02d} Seconds"

# -------------------------------
# Amount calculation
# -------------------------------
rate_per_hour = float(game["rate_per_hour"])
amount = round((elapsed_seconds / 3600) * rate_per_hour, 2)

# -------------------------------
# Display
# -------------------------------
st.subheader(f"👤 {game['orders']['table_name']}")

st.metric("🎱 Pool Rate", f"₹ {rate_per_hour} / Hour")
st.metric("🕒 Started At", start_utc.astimezone(IST).strftime("%I:%M:%S %p"))
st.metric("⏱ Time Elapsed", elapsed_str)
st.metric("💰 Total Spend", f"₹ {amount}")

# -------------------------------
# Live second tick (NO REFRESH)
# -------------------------------
time.sleep(1)
st.rerun()
