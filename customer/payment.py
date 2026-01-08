import streamlit as st
from supabase_client import supabase
from utils.bill import generate_bill_pdf


def payment_page(order_id):
    order = supabase.table("orders").select("*").eq("id", order_id).single().execute()
    tenant = supabase.table("tenants").select("*").eq("id", order.data["tenant_id"]).single().execute()

    st.title(tenant.data["name"])
    st.subheader(f"Order #{order.data['order_number']}")

    if tenant.data.get("upi_qr_url"):
        st.image(tenant.data["upi_qr_url"], width=250)

    pdf = generate_bill_pdf(order_id)

    st.download_button(
        "Download Bill",
        pdf,
        file_name=f"bill_{order.data['order_number']}.pdf",
        mime="application/pdf"
    )
