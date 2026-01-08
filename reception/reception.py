import streamlit as st
from supabase_client import supabase


def reception_screen(tenant_id):
    st.title("🧾 Reception / Cashier")

    orders = supabase.table("orders") \
        .select("*") \
        .eq("tenant_id", tenant_id) \
        .order("created_at", desc=True) \
        .execute()

    if not orders.data:
        st.info("No orders found")
        return

    for order in orders.data:
        # -----------------------------
        # SAFETY DEFAULTS
        # -----------------------------
        total = float(order.get("total") or 0)
        discount_amount_db = float(order.get("discount_amount") or 0)
        discount_percent_db = float(order.get("discount_percent") or 0)

        subtotal = total + discount_amount_db

        with st.expander(
            f"Order #{order['id']} | {order.get('customer_name','Guest')} | ₹{total:.2f}"
        ):
            # -----------------------------
            # TABLE ASSIGNMENT
            # -----------------------------
            table_name = st.text_input(
                "Table Name / Number",
                value=order.get("table_name") or "",
                key=f"table_{order['id']}"
            )

            st.divider()

            # -----------------------------
            # DISCOUNT SECTION
            # -----------------------------
            st.subheader("🏷 Adjust Bill Discount")

            if subtotal <= 0:
                st.warning("Invalid subtotal. Cannot apply discount.")
                continue

            col1, col2 = st.columns(2)

            with col1:
                discount_percent = st.number_input(
                    "Discount (%)",
                    min_value=0.0,
                    max_value=100.0,
                    value=discount_percent_db,
                    step=1.0,
                    key=f"dp_{order['id']}"
                )

            with col2:
                discount_amount = st.number_input(
                    "Discount Amount (₹)",
                    min_value=0.0,
                    max_value=subtotal,
                    value=discount_amount_db,
                    step=1.0,
                    key=f"da_{order['id']}"
                )

            # -----------------------------
            # CALCULATION LOGIC
            # -----------------------------
            if discount_percent > 0:
                final_discount_amount = round(subtotal * discount_percent / 100, 2)
                final_discount_percent = round(discount_percent, 2)
            elif discount_amount > 0:
                final_discount_amount = round(discount_amount, 2)
                final_discount_percent = round(
                    (final_discount_amount / subtotal) * 100, 2
                )
            else:
                final_discount_amount = 0.0
                final_discount_percent = 0.0

            final_total = round(subtotal - final_discount_amount, 2)
            if final_total < 0:
                final_total = 0.0

            # -----------------------------
            # DISPLAY BILL
            # -----------------------------
            st.markdown(
                f"""
                **Subtotal:** ₹{subtotal:.2f}  
                **Discount:** ₹{final_discount_amount:.2f} ({final_discount_percent:.2f}%)  
                **Final Total:** ₹{final_total:.2f}
                """
            )

            # -----------------------------
            # SAVE BILL
            # -----------------------------
            if st.button("💾 Save Bill", key=f"save_{order['id']}"):
                update_payload = {
                    "table_name": table_name,
                    "discount_percent": float(final_discount_percent),
                    "discount_amount": float(final_discount_amount),
                    "total": float(final_total)
                }

                supabase.table("orders") \
                    .update(update_payload) \
                    .eq("id", order["id"]) \
                    .execute()

                st.success("Bill updated successfully")
                st.rerun()

            st.divider()

            # -----------------------------
            # PAYMENT & STATUS
            # -----------------------------
            st.write(f"💳 Payment Status: **{order.get('payment_status','pending')}**")
            st.write(f"📦 Order Status: **{order.get('status','open')}**")

            if order.get("payment_status") == "pending":
                if st.button("✅ Mark Paid", key=f"paid_{order['id']}"):
                    supabase.table("orders") \
                        .update({"payment_status": "paid"}) \
                        .eq("id", order["id"]) \
                        .execute()
                    st.rerun()

            if order.get("status") == "open":
                if st.button("🚫 Close Order", key=f"close_{order['id']}"):
                    supabase.table("orders") \
                        .update({"status": "completed"}) \
                        .eq("id", order["id"]) \
                        .execute()
                    st.rerun()
