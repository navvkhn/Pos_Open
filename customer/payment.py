import streamlit as st
from supabase_client import supabase
from utils.bill import generate_bill_pdf

def payment_page(order_id):
    order = supabase.table("orders").select("*").eq("id", order_id).single().execute()
    tenant = supabase.table("tenants").select("*").eq("id", order.data["tenant_id"]).single().execute()

    st.image(tenant.data["logo_url"], width=120)
    st.title(tenant.data["name"])

    st.subheader("💳 Please pay to confirm your order")

    if tenant.data.get("upi_qr_url"):
        st.image(tenant.data["upi_qr_url"], width=250)

    st.info("Pay using UPI and show confirmation to counter")

    pdf = generate_bill_pdf(order_id)

    st.download_button(
        "⬇ Download Bill",
        data=pdf,
        file_name="bill.pdf",
        mime="application/pdf"
    )
