import streamlit as st
from supabase_client import supabase
from utils.bill import generate_bill_pdf


def payment_page(order_id):
    st.set_page_config(layout="wide")

    # --------------------------------------------------
    # 🎨 MOBILE FRIENDLY CSS (SAFE)
    # --------------------------------------------------
    st.markdown("""
    <style>
    button {
        min-height: 48px;
        font-size: 16px;
    }
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 5rem;
    }
    img {
        display: block;
        margin-left: auto;
        margin-right: auto;
    }
    </style>
    """, unsafe_allow_html=True)

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
    # HEADER (CENTERED)
    # --------------------------------------------------
    if tenant.data.get("logo_url"):
        st.image(tenant.data["logo_url"], width=110)

    st.markdown(
        f"<h2 style='text-align:center;margin-bottom:4px'>{tenant_name}</h2>",
        unsafe_allow_html=True
    )

    st.markdown(
        "<p style='text-align:center;font-size:16px'>💳 Please pay to confirm your order</p>",
        unsafe_allow_html=True
    )

    st.divider()

    # --------------------------------------------------
    # UPI QR (RESPONSIVE)
    # --------------------------------------------------
    if tenant.data.get("upi_qr_url"):
        st.image(
            tenant.data["upi_qr_url"],
            use_container_width=True
        )

    st.info("Pay using UPI and show confirmation to counter")

    st.divider()

    # --------------------------------------------------
    # DOWNLOAD BILL (BIG BUTTON)
    # --------------------------------------------------
    pdf = generate_bill_pdf(order_id)

    st.download_button(
        "⬇ Download Bill",
        data=pdf,
        file_name=f"bill_{order_id}.pdf",
        mime="application/pdf",
        use_container_width=True
    )

    st.divider()

    # --------------------------------------------------
    # 🔁 BACK TO MENU / NEW ORDER
    # --------------------------------------------------
    if st.button(
        "🔁 Order Again / Back to Menu",
        use_container_width=True
    ):
        # Clear session order state
        st.session_state.pop("order_id", None)

        # Reset query params
        st.query_params.clear()
        st.query_params["menu"] = tenant_name.replace(" ", "%20")

        st.rerun()
