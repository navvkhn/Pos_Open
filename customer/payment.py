import streamlit as st
from supabase_client import supabase
from utils.bill import generate_bill_pdf


def payment_page(order_id):
    # --------------------------------------------------
    # FETCH ORDER & TENANT
    # --------------------------------------------------
    order = supabase.table("orders") \
        .select("*") \
        .eq("id", order_id) \
        .single() \
        .execute()

    tenant = supabase.table("tenants") \
        .select("*") \
        .eq("id", order.data["tenant_id"]) \
        .single() \
        .execute()

    tenant_name = tenant.data["name"]

    # --------------------------------------------------
    # HEADER
    # --------------------------------------------------
    if tenant.data.get("logo_url"):
        st.image(tenant.data["logo_url"], width=120)

    st.title(tenant_name)
    st.subheader("💳 Please pay to confirm your order")

    # --------------------------------------------------
    # UPI QR
    # --------------------------------------------------
    if tenant.data.get("upi_qr_url"):
        st.image(tenant.data["upi_qr_url"], width=250)

    st.info("Pay using UPI and show confirmation to counter")

    # --------------------------------------------------
    # DOWNLOAD BILL
    # --------------------------------------------------
    pdf = generate_bill_pdf(order_id)

    st.download_button(
        "⬇ Download Bill",
        data=pdf,
        file_name=f"bill_{order_id}.pdf",
        mime="application/pdf"
    )

    st.divider()

    # --------------------------------------------------
    # 🔁 BACK TO MENU / NEW ORDER
    # --------------------------------------------------
    if st.button("🔁 Order Again / Back to Menu"):
        # Clear session order state
        st.session_state.pop("order_id", None)

        # Reset query params
        st.query_params.clear()
        st.query_params["menu"] = tenant_name.replace(" ", "%20")

        st.rerun()
