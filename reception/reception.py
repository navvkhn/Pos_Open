import streamlit as st
from supabase_client import supabase
from datetime import datetime
import pytz
import time

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
IST = pytz.timezone("Asia/Kolkata")
time.sleep(0.3)  # prevent rapid reruns hitting Supabase


def reception_screen(tenant_id):
    st.title("🧾 Reception / Cashier")

    # --------------------------------------------------
    # 🎨 MOBILE + DARK MODE SAFE CSS
    # --------------------------------------------------
    st.markdown("""
    <style>
    .order-box {
        background-color: var(--secondary-background-color);
        border: 1px solid rgba(128,128,128,0.4);
        border-radius: 12px;
        padding: 12px;
        margin-bottom: 14px;
    }
    button {
        min-height: 48px;
        font-size: 16px;
    }
    </style>
    """, unsafe_allow_html=True)

    # --------------------------------------------------
    # 🔄 REFRESH
    # --------------------------------------------------
    if st.button("🔄 Refresh"):
        st.rerun()

    # --------------------------------------------------
    # 📅 TODAY RANGE (IST → UTC)
    # --------------------------------------------------
    today_ist = datetime.now(IST).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    today_utc = today_ist.astimezone(pytz.utc)

    # --------------------------------------------------
    # 📊 TOP METRICS
    # --------------------------------------------------
    unpaid = supabase.table("orders") \
        .select("id", count="exact") \
        .eq("tenant_id", tenant_id) \
        .eq("payment_status", "pending") \
        .gte("created_at", today_utc.isoformat()) \
        .execute()

    open_orders = supabase.table("orders") \
        .select("id", count="exact") \
        .eq("tenant_id", tenant_id) \
        .eq("status", "open") \
        .gte("created_at", today_utc.isoformat()) \
        .execute()

    prepared = supabase.table("orders") \
        .select("id", count="exact") \
        .eq("tenant_id", tenant_id) \
        .eq("status", "prepared") \
        .gte("created_at", today_utc.isoformat()) \
        .execute()

    today_paid = supabase.table("orders") \
        .select("total") \
        .eq("tenant_id", tenant_id) \
        .eq("payment_status", "paid") \
        .gte("created_at", today_utc.isoformat()) \
        .execute()

    today_revenue = sum(float(o["total"]) for o in today_paid.data)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💳 Unpaid", unpaid.count)
    c2.metric("🕒 Open", open_orders.count)
    c3.metric("🍳 Prepared", prepared.count)
    c4.metric("₹ Revenue", f"{today_revenue:.2f}")

    st.divider()

    # --------------------------------------------------
    # 🧾 FETCH TODAY'S ORDERS
    # --------------------------------------------------
    orders = supabase.table("orders") \
        .select("""
            *,
            order_items (
                product_name
            )
        """) \
        .eq("tenant_id", tenant_id) \
        .gte("created_at", today_utc.isoformat()) \
        .order("created_at", desc=True) \
        .execute()

    if not orders.data:
        st.info("No orders today")
        return

    # --------------------------------------------------
    # 🧾 ORDERS LIST
    # --------------------------------------------------
    for order in orders.data:
        order_id = order["id"]                     # INTERNAL
        order_no = order.get("order_number", "—") # DISPLAY
        status = order.get("status")
        payment_status = order.get("payment_status")

        total = float(order.get("total") or 0)
        discount_amount_db = float(order.get("discount_amount") or 0)
        discount_percent_db = float(order.get("discount_percent") or 0)
        subtotal = total + discount_amount_db

        # Created time IST
        try:
            created_ist = (
                datetime.fromisoformat(
                    order["created_at"].replace("Z", "+00:00")
                )
                .astimezone(IST)
                .strftime("%I:%M %p")
            )
        except Exception:
            created_ist = "—"

        unpaid_flag = "🔴 " if payment_status == "pending" else ""

        # ✅ MOBILE FRIENDLY HEADER
        header = f"{unpaid_flag}Order #{order_no} | ₹{total:.2f}"

        with st.expander(header):
            is_open = status == "open"

            st.markdown("<div class='order-box'>", unsafe_allow_html=True)

            st.write(f"👤 **Customer:** {order.get('customer_name','Guest')}")
            st.write(f"🕒 **Time:** {created_ist}")

            if not is_open:
                st.warning("🔒 Order closed. Editing disabled.")

            # -------------------------
            # TABLE NAME
            # -------------------------
            table_name = st.text_input(
                "🍽 Table Name / Number",
                value=order.get("table_name") or "",
                disabled=not is_open,
                key=f"table_{order_id}"
            )

            # -------------------------
            # DISCOUNT (ONLY IF OPEN)
            # -------------------------
            if is_open:
                st.subheader("🏷 Discount")

                discount_percent_input = st.number_input(
                    "Discount %",
                    0.0, 100.0,
                    value=discount_percent_db,
                    step=1.0,
                    key=f"dp_{order_id}"
                )

                discount_amount_input = st.number_input(
                    "Discount ₹",
                    0.0, subtotal,
                    value=discount_amount_db,
                    step=1.0,
                    key=f"da_{order_id}"
                )

                if discount_percent_input > 0:
                    final_discount_amount = round(
                        subtotal * discount_percent_input / 100, 2
                    )
                    final_discount_percent = discount_percent_input
                elif discount_amount_input > 0:
                    final_discount_amount = discount_amount_input
                    final_discount_percent = round(
                        (final_discount_amount / subtotal) * 100, 2
                    )
                else:
                    final_discount_amount = 0.0
                    final_discount_percent = 0.0

                final_total = round(subtotal - final_discount_amount, 2)

                st.markdown(
                    f"""
                    **Subtotal:** ₹{subtotal:.2f}  
                    **Discount:** ₹{final_discount_amount:.2f}  
                    **Total:** ₹{final_total:.2f}
                    """
                )

                # -------------------------
                # 💾 SAVE BILL
                # -------------------------
                if st.button("💾 Save Bill", key=f"save_{order_id}", use_container_width=True):
                    supabase.table("orders") \
                        .update({
                            "table_name": table_name,
                            "discount_percent": float(final_discount_percent),
                            "discount_amount": float(final_discount_amount),
                            "total": float(final_total)
                        }) \
                        .eq("id", order_id) \
                        .eq("status", "open") \
                        .execute()

                    st.success("✅ Bill updated")
                    st.rerun()

            st.divider()

            # -------------------------
            # PAYMENT & CLOSE
            # -------------------------
            if is_open:
                if payment_status == "pending":
                    if st.button("✅ Mark Paid", key=f"paid_{order_id}", use_container_width=True):
                        supabase.table("orders") \
                            .update({"payment_status": "paid"}) \
                            .eq("id", order_id) \
                            .eq("status", "open") \
                            .execute()
                        st.rerun()

                if st.button("🚫 Close Order", key=f"close_{order_id}", use_container_width=True):
                    supabase.table("orders") \
                        .update({"status": "completed"}) \
                        .eq("id", order_id) \
                        .eq("status", "open") \
                        .execute()
                    st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)
