import streamlit as st
from supabase_client import supabase

def settings(tenant_id):
    st.title("🏷 Cafe Branding & Payments")

    tenant = supabase.table("tenants") \
        .select("*") \
        .eq("id", tenant_id) \
        .single() \
        .execute()

    logo = st.file_uploader("Cafe Logo", type=["png", "jpg"])
    upi_qr = st.file_uploader("UPI QR Code", type=["png", "jpg"])
    address = st.text_area("Cafe Address", value=tenant.data.get("address", ""))
    contact = st.text_input("Contact Number", value=tenant.data.get("contact", ""))

    if st.button("Save Settings"):
        updates = {
            "address": address,
            "contact": contact
        }

        if logo:
            path = f"{tenant_id}/logo.png"
            supabase.storage.from_("branding").upload(
                path, logo.getvalue(),
                {"content-type": logo.type}, upsert=True
            )
            updates["logo_url"] = supabase.storage.from_("branding").get_public_url(path)

        if upi_qr:
            path = f"{tenant_id}/upi_qr.png"
            supabase.storage.from_("branding").upload(
                path, upi_qr.getvalue(),
                {"content-type": upi_qr.type}, upsert=True
            )
            updates["upi_qr_url"] = supabase.storage.from_("branding").get_public_url(path)

        supabase.table("tenants").update(updates).eq("id", tenant_id).execute()
        st.success("✅ Branding updated")
