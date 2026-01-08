import streamlit as st
from supabase_client import supabase
from datetime import datetime, timezone


def kitchen_screen(tenant_id):
    # 🔄 Auto refresh every 10 seconds
    st.autorefresh(interval=10_000, key="kitchen_refresh")

    # --------------------------------------------------
    # Fetch tenant branding (LOGO + NAME)
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

    now = datetime.now(timezone.utc)

    for order in orders.data:
        # Extra safety
        if order["status"] != "open":
            continue

        created_at_raw = order["created_at"]

        # Handle all timestamp formats safely
        created_at = (
            datetime.fromisoformat(created_at_raw.replace("Z", "+00:00"))
            if isinstance(created_at_raw, str)
            else created_at_raw
        )

        pending_minutes = int(
            (now - created_at).total_seconds() // 60
        )

        # ⏱ Priority indicator
        if pending_minutes >= 15:
            st.error(f"🔥 Order #{order['id']}  •  Pending {pending_minutes} min")
        elif pending_minutes >= 7:
            st.warning(f"⏳ Order #{order['id']}  •  Pending {pending_minutes} min")
        else:
            st.info(f"🕒 Order #{order['id']}  •  Pending {pending_minutes} min")

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
