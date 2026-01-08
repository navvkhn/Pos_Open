import streamlit as st
from supabase_client import supabase
from datetime import datetime, timezone

def kitchen_screen(tenant_id):
    st.title("🍳 Kitchen Orders")

    # -----------------------------
    # Auto refresh every 10 seconds
    # -----------------------------
    st.autorefresh(interval=10_000, key="kitchen_refresh")

    orders = supabase.table("orders") \
        .select("id, created_at") \
        .eq("tenant_id", tenant_id) \
        .eq("status", "open") \
        .order("created_at") \
        .execute()

    if not orders.data:
        st.success("✅ No pending orders")
        return

    for order in orders.data:
        created_at = datetime.fromisoformat(
            order["created_at"].replace("Z", "+00:00")
        )

        now = datetime.now(timezone.utc)
        pending_minutes = int((now - created_at).total_seconds() / 60)

        # -----------------------------
        # Visual priority indicator
        # -----------------------------
        if pending_minutes >= 15:
            st.error(f"🔥 Order #{order['id']} — Pending {pending_minutes} min")
        elif pending_minutes >= 7:
            st.warning(f"⏳ Order #{order['id']} — Pending {pending_minutes} min")
        else:
            st.info(f"🕒 Order #{order['id']} — Pending {pending_minutes} min")

        items = supabase.table("order_items") \
            .select("*") \
            .eq("order_id", order["id"]) \
            .execute()

        for item in items.data:
            st.write(f"• {item['quantity']} × {item['product_name']}")

        st.divider()
