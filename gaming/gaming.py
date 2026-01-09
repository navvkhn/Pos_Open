import streamlit as st
from supabase_client import supabase
from datetime import datetime
import time

st.set_page_config(layout="centered")

st.title("🎱 Pool Table Live")

games = supabase.table("games") \
    .select("*") \
    .eq("status", "running") \
    .order("created_at", desc=True) \
    .limit(1) \
    .execute()

if not games.data:
    st.warning("No active game")
    time.sleep(2)
    st.rerun()

game = games.data[0]

start = datetime.fromisoformat(game["start_time"].replace("Z", ""))
now = datetime.utcnow()

paused_seconds = game.get("paused_seconds", 0)
elapsed_seconds = (now - start).total_seconds() - paused_seconds
minutes = max(0, int(elapsed_seconds / 60))
amount = round((minutes / 30) * 100, 2)

st.metric("Status", "▶ RUNNING")
st.metric("Time Played", f"{minutes} mins")
st.metric("Amount", f"₹ {amount}")

time.sleep(2)
st.rerun()
