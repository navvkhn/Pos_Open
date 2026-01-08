import streamlit as st
from supabase_client import supabase
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import time
import math


def kitchen_screen(tenant_id):
    # ----------------------------------
    # Auto refresh every 15 seconds
    # ----------------------------------
    if "last_refresh" not in st.session_state:
        st.session_state.last_refresh = time.time()

    if time.time() - st.session_state.last_refresh > 15:
        st.session_state.last_refresh = time.time()
        st.experimental_rerun()

    IST = ZoneInfo("Asia/Kolkata")

    # ----------------------------------
    # Tenant branding
    # ----------------------------------
    tenant = supabase.table("tenants") \
        .select("name, logo_url") \
        .eq("id", tenant_id) \
        .single() \
        .execute()

    if tenant.data.get("logo_url"):
        st.image(tenant.data["logo_url"], width=120)

    st.markdown(f"## 🍳 {tenant.data['name']} – Kitchen")
    st.divider()

    # ----------------------------------
    # Fetch ONLY open orders
    # ----------------------------------
    orders = supabase.table("orders") \
        .select("id, created_at, table_name, customer_name") \
        .eq("tenant_id", tenant_id) \
        .eq("status", "open") \
        .order("created_at") \
        .execute()

    if not orders.data:
        st.success("✅ No open kitchen orders")
        return

    now = datetime.now(timezone.utc).astimezone(IST)

    # ----------------------------------
    # Grid layout (4 per row)
    # ----------------------------------
    cols_per_row = 4
    rows = math.ceil(len(orders.data) / cols_per_row)

    for r in range(rows):
        cols = st.columns(cols_per_row)

        for c in range(cols_per_row):
            index = r * cols_per_row + c
            if index >= len(orders.data):
                break

            order = orders.data[index]

            created_ist = datetime.fromisoformat(
                order["created_at"].replace("Z", "+00:00")
            ).astimezone(IST)

            pending_minutes = int(
                (now - created_ist).total_seconds() // 60
            )

            time_str = created_ist.strftime("%I:%M %p")

            table = order.get("table_name") or "—"
            customer = order.get("customer_name") or "Guest"

            # ----------------------------------
            # Card color based on urgency
            # ----------------------------------
            if pending_minutes >= 15:
                color = "🔴"
            elif pending_minutes >= 7:
                color = "🟡"
            else:
                color = "🟢"

            with cols[c]:
                st.markdown(
                    f"""
                    ### {color} Order #{order['id']}
                    **Table:** {table}  
                    **Customer:** {customer}  
                    **Time:** {time_str} IST  
                    **Pending:** {pending_minutes} min
                    """
                )

                items = supabase.table("order_items") \
                    .select("product_name, quantity") \
                    .eq("order_id", order["id"]) \
                    .execute()

                for item in items.data:
                    st.write(f"• {item['quantity']} × {item['product_name']}")

                st.markdown("---")
