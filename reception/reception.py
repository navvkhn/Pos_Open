import streamlit as st
from supabase_client import supabase
from postgrest.exceptions import APIError
from datetime import datetime
import pytz

IST = pytz.timezone("Asia/Kolkata")


def reception_screen(tenant_id):
    st.title("🧾 Reception / Cashier")

    # --------------------------------------------------
    # 📊 TOP DASHBOARD METRICS
    # --------------------------------------------------
    today_ist = datetime.now(IST).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    today_utc = today_ist.astimezone(pytz.utc)

    unpaid = supabase.table("orders") \
        .select("id", count="exact") \
        .eq("tenant_id", tenant_id) \
        .eq("payment_status", "pending") \
        .execute()

    open_orders = supabase.table("orders") \
        .select("id", count="exact") \
        .eq("tenant_id", tenant_id) \
        .eq("status", "open") \
        .execute()

    prepared = supabase.table("orders") \
        .select("id", count="exact") \
        .eq("tenant_id", tenant_id) \
        .eq("status", "prepared") \
        .execute()

    today_paid = supabase.table("orders") \
        .select("total") \
        .eq("tenant_id", tenant_id) \
        .eq("payment_status", "paid") \
        .gte("created_at", today_utc.isoformat()) \
        .execute()

    today_revenue = sum(float(o["total"]) for o in today_paid.data)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💳 Unpaid Orders", unpaid.count)
    c2.metric("🕒 Open Orders", open_orders.count)
    c3.metric("🍳 Prepared", prepared.count)
    c4.metric("₹ Today Revenue", f"{today_revenue:.2f}")

    st.divider()

    # --------------------------------------------------
    # ORDERS LIST
    # --------------------------------------------------
    orders = supabase.table("orders") \
        .select("*") \
        .eq("tenant_id", tenant_id) \
        .order("created_at", desc=True) \
        .execute()

    if not orders.data:
        st.info("No orders found")
        return

    for order in orders.data:
        order_id = order["id"]

        total = float(order.get("total") or 0)
        discount_amount_db = float(order.get("discount_amount") or 0)
        discount_percent_db = float(order.get("discount_percent") or 0)
        subtotal = total + discount_amount_db

        with st.expander(
            f"Order #{order_id} | {order.get('customer_name','Guest')} | ₹{total:.2f}"
        ):
            if order.get("status") != "open":
                st.info("Order closed. Editing disabled.")
                continue

            # -------------------------
            # TABLE NAME
            # -------------------------
            table_name = st.text_input(
                "Table Name / Number",
                value=order.get("table_name") or "",
                key=f"table_{order_id}"
            )

            st.divider()

            # -------------------------
            # DISCOUNT INPUTS
            # -------------------------
            st.subheader("🏷 Adjust Discount")

            col1, col2 = st.columns(2)

            with col1:
                discount_percent_input = st.number_input(
                    "Discount %",
                    0.0, 100.0,
                    value=discount_percent_db,
                    step=1.0,
                    key=f"dp_{order_id}"
                )

            with col2:
                discount_amount_input = st.number_input(
                    "Discount Amount (₹)",
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
                **Discount:** ₹{final_discount_amount:.2f} ({final_discount_percent:.2f}%)  
                **Final Total:** ₹{final_total:.2f}
                """
            )

            # -------------------------
            # SAVE BILL
            # -------------------------
            if st.button("💾 Save Bill", key=f"save_{order_id}"):
                payload = {
                    "table_name": table_name,
                    "discount_percent": float(final_discount_percent),
                    "discount_amount": float(final_discount_amount),
                    "total": float(final_total)
                }

                try:
                    supabase.table("orders") \
                        .update(payload) \
                        .eq("id", order_id) \
                        .execute()

                    st.success("Bill updated successfully")
                    st.rerun()

                except APIError as e:
                    st.error("Database rejected the update")
                    st.code(e.message)

            st.divider()

            # -------------------------
            # PAYMENT
            # -------------------------
            if order.get("payment_status") == "pending":
                if st.button("✅ Mark Paid", key=f"paid_{order_id}"):
                    supabase.table("orders") \
                        .update({"payment_status": "paid"}) \
                        .eq("id", order_id) \
                        .execute()
                    st.rerun()

            # -------------------------
            # CLOSE ORDER
            # -------------------------
            if st.button("🚫 Close Order", key=f"close_{order_id}"):
                supabase.table("orders") \
                    .update({"status": "completed"}) \
                    .eq("id", order_id) \
                    .execute()
                st.rerun()
