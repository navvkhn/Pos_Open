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
        subtotal = order["total"] + order.get("discount_amount", 0)

        with st.expander(
            f"Order #{order['id']} | {order.get('customer_name','')} | ₹{order['total']}"
        ):
            # --------------------------------------------------
            # TABLE ASSIGNMENT
            # --------------------------------------------------
            table_name = st.text_input(
                "Table Name / Number",
                value=order.get("table_name", ""),
                key=f"table_{order['id']}"
            )

            # --------------------------------------------------
            # DISCOUNT ADJUSTMENT
            # --------------------------------------------------
            st.subheader("🏷 Adjust Discount")

            col1, col2 = st.columns(2)

            with col1:
                discount_percent = st.number_input(
                    "Discount %",
                    min_value=0.0,
                    max_value=100.0,
                    value=float(order.get("discount_percent", 0)),
                    key=f"dp_{order['id']}"
                )

            with col2:
                discount_amount = st.number_input(
                    "Discount Amount (₹)",
                    min_value=0.0,
                    max_value=float(subtotal),
                    value=float(order.get("discount_amount", 0)),
                    key=f"da_{order['id']}"
                )

            # --------------------------------------------------
            # CALCULATE FINAL VALUES
            # --------------------------------------------------
            if discount_percent > 0:
                final_discount_amount = round(subtotal * discount_percent / 100, 2)
                final_discount_percent = discount_percent
            elif discount_amount > 0:
                final_discount_amount = discount_amount
                final_discount_percent = round((discount_amount / subtotal) * 100, 2)
            else:
                final_discount_amount = 0
                final_discount_percent = 0

            final_total = round(subtotal - final_discount_amount, 2)
            if final_total < 0:
                final_total = 0

            st.markdown(
                f"""
                **Subtotal:** ₹{subtotal:.2f}  
                **Discount:** ₹{final_discount_amount:.2f} ({final_discount_percent:.1f}%)  
                **Final Total:** ₹{final_total:.2f}
                """
            )

            # --------------------------------------------------
            # SAVE BILL
            # --------------------------------------------------
            if st.button("💾 Save Bill", key=f"save_bill_{order['id']}"):
                supabase.table("orders") \
                    .update({
                        "table_name": table_name,
                        "discount_percent": final_discount_percent,
                        "discount_amount": final_discount_amount,
                        "total": final_total
                    }) \
                    .eq("id", order["id"]) \
                    .execute()

                st.success("Bill updated successfully")
                st.rerun()

            # --------------------------------------------------
            # PAYMENT & STATUS
            # --------------------------------------------------
            st.divider()

            st.write(f"Payment Status: {order['payment_status']}")
            st.write(f"Order Status: {order['status']}")

            if order["payment_status"] == "pending":
                if st.button("✅ Mark Paid", key=f"paid_{order['id']}"):
                    supabase.table("orders") \
                        .update({"payment_status": "paid"}) \
                        .eq("id", order["id"]) \
                        .execute()
                    st.rerun()

            if order["status"] == "open":
                if st.button("🚫 Close Order", key=f"close_{order['id']}"):
                    supabase.table("orders") \
                        .update({"status": "completed"}) \
                        .eq("id", order["id"]) \
                        .execute()
                    st.rerun()
