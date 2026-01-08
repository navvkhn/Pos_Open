import streamlit as st
from supabase_client import supabase
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import time

def kitchen_screen(tenant_id):
    if "last_refresh" not in st.session_state:
        st.session_state.last_refresh = time.time()

    if time.time() - st.session_state.last_refresh > 15:
        st.session_state.last_refresh = time.time()
        st.experimental_rerun()

    IST = ZoneInfo("Asia/Kolkata")

    tenant = supabase.table("tenants") \
        .select("name, logo_url") \
        .eq("id", tenant_id) \
        .single() \
        .execute()

    if tenant.data.get("logo_url"):
        st.image(tenant.data["logo_url"], width=120)

    st.markdown(f"## 🍳 {tenant.data['name']} – Kitchen")
    st.divider()

    orders = supabase.table("orders") \
        .select("id, created_at, table_name, customer_name") \
        .eq("tenant_id", tenant_id) \
        .eq("status", "open") \
        .order("created_at") \
        .execute()

    if not orders.data:
        st.success("No open orders")
        return

    now = datetime.now(timezone.utc).astimezone(IST)

    for order in orders.data:
        created = datetime.fromisoformat(
            order["created_at"].replace("Z", "+00:00")
        ).astimezone(IST)

        mins = int((now - created).total_seconds() // 60)
        time_str = created.strftime("%I:%M %p IST")

        st.info(
            f"Order #{order['id']} | Table: {order.get('table_name','—')} | "
            f"{order.get('customer_name','Guest')} | {time_str} | {mins} min"
        )

        items = supabase.table("order_items") \
            .select("product_name, quantity") \
            .eq("order_id", order["id"]) \
            .execute()

        for i in items.data:
            st.write(f"• {i['quantity']} × {i['product_name']}")

        st.divider()
