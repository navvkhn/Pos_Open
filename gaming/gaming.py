import streamlit as st
from supabase_client import supabase
from datetime import datetime
import pytz
import time
from dateutil.parser import isoparse

IST = pytz.timezone("Asia/Kolkata")


def gaming_screen(tenant_id):
    st.set_page_config(layout="wide")
    st.title("🎱 Pool Table Dashboard")

    st.markdown("""
    <style>
    .game-card {
        background-color: var(--secondary-background-color);
        border: 2px solid rgba(128,128,128,0.4);
        border-radius: 14px;
        padding: 16px;
        margin-bottom: 16px;
    }
    button {
        min-height: 48px;
        font-size: 16px;
    }
    </style>
    """, unsafe_allow_html=True)

    # 🔄 Auto refresh every 10 sec
    if "game_refresh" not in st.session_state:
        st.session_state.game_refresh = time.time()

    if time.time() - st.session_state.game_refresh > 10:
        st.session_state.game_refresh = time.time()
        st.rerun()

    # --------------------------------------------------
    # FETCH ACTIVE GAME
    # --------------------------------------------------
    game = supabase.table("games") \
        .select("*") \
        .eq("tenant_id", tenant_id) \
        .eq("status", "running") \
        .single() \
        .execute()

    if not game.data:
        st.info("No active game")

        if st.button("▶ Start Pool Game"):
            supabase.table("games").insert({
                "tenant_id": tenant_id,
                "start_time": datetime.utcnow().isoformat(),
                "rate_per_30_min": 100
            }).execute()
            st.rerun()

        return

    game = game.data

    # --------------------------------------------------
    # TIME CALCULATION
    # --------------------------------------------------
    start_utc = isoparse(game["start_time"])
    start_ist = start_utc.astimezone(IST)
    now_ist = datetime.now(IST)

    minutes = int((now_ist - start_ist).total_seconds() / 60)
    amount = (minutes / 30) * float(game["rate_per_30_min"])
    amount = round(amount, 2)

    st.markdown(
        f"""
        <div class="game-card">
        <h3>🎱 Pool Table</h3>
        <b>Start Time:</b> {start_ist.strftime('%I:%M %p')}<br>
        <b>Elapsed:</b> {minutes} minutes<br>
        <b>Rate:</b> ₹{game['rate_per_30_min']} / 30 mins<br>
        <h2>₹ {amount}</h2>
        </div>
        """,
        unsafe_allow_html=True
    )

    if st.button("⏹ Stop Game"):
        supabase.table("games").update({
            "end_time": datetime.utcnow().isoformat(),
            "total_minutes": minutes,
            "total_amount": amount,
            "status": "stopped"
        }).eq("id", game["id"]).execute()

        st.success("Game stopped. Send to reception for billing.")
        st.rerun()
