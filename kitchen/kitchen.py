import streamlit as st
from supabase_client import supabase
from datetime import datetime, timezone
from zoneinfo import ZoneInfo


def kitchen_screen(tenant_id):
    # 🔄 Auto refresh every 10 seconds
    st.autorefresh(interval=10_000, key="kitchen_refresh")

    IST = ZoneInfo("Asia/Kolkata")

    # --------------------------------------------------
    # Fetch tenant branding
    # --------------------------------------------------
    tenant = supabase.table("tenants") \
        .select("name, logo_url") \
        .eq("id", tenant_id) \
        .single() \
        .execute()

    if tenant.data.get("logo_url"):
        st.image(tenant.data["logo_url"], width=120)

    st.markdown(f"## 🍳 {tenant.data['name']} – Kitchen")
    st.divider()

    # --------------------------------------------------
    # ONLY OPEN ORDERS
    # --------------------------------------------------
    orders = supabase.table("orders") \
        .select("id, created_at, status") \
        .eq("tenant_id", tenant_id) \
        .eq("status", "open") \
        .order("created_at") \
        .execute()

    if not orders.data:
        st.success("✅ No open kitchen orders")
        return

    now_utc = datetime.now(timezone.utc)
    now_ist = now_utc.astimezone(IST)

    for order in orders.data:
        created_at_raw = order.get("created_at")

        if not created_at_raw:
            st.warning(f"Order #{order['id']} — time not recorded")
            continue

        # Parse UTC time from DB
        created_utc = datetime.fromisoformat(
            created_at_raw.replace("Z", "+00:00")
        )

        # Convert to IST
        created_ist = created_utc.astimezone(IST)

        pending_minutes = int(
            (now_ist - created_ist).total_seconds() // 60
        )

        order_time = created_ist.strftime("%d %b %Y • %I:%M %p IST")

        # -----------------------------
        # Header with IST time + minutes
        # -----------------------------
        if pending_minutes >= 15:
            st.error(
                f"🔥 Order #{order['id']}  |  {order_time}  |  Pending {pending_minutes} min"
            )
        elif pending_minutes >= 7:
            st.warning(
                f"⏳ Order #{order['id']}  |  {order_time}  |  Pending {pending_minutes} min"
            )
        else:
            st.info(
                f"🕒 Order #{order['id']}  |  {order_time}  |  Pending {pending_minutes} min"
            )

        # --------------------------------------------------
        # Order items
        # --------------------------------------------------
        items = supabase.table("order_items") \
            .select("product_name, quantity") \
            .eq("order_id", order["id"]) \
            .execute()

        for item in items.data:
            st.write(f"• {item['quantity']} × {item['product_name']}")

        st.divider()
