import streamlit as st
from supabase_client import supabase


def settings(tenant_id):
    st.title("🏷 Cafe Branding & Payments")

    # ----------------------------------
    # Fetch tenant
    # ----------------------------------
    tenant = supabase.table("tenants") \
        .select("*") \
        .eq("id", tenant_id) \
        .single() \
        .execute()

    # ----------------------------------
    # Uploads
    # ----------------------------------
    logo = st.file_uploader("Cafe Logo", type=["png", "jpg"])
    upi_qr = st.file_uploader("UPI QR Code", type=["png", "jpg"])

    # ----------------------------------
    # Text settings
    # ----------------------------------
    address = st.text_area(
        "Cafe Address",
        value=tenant.data.get("address", "")
    )

    contact = st.text_input(
        "Contact Number",
        value=tenant.data.get("contact", "")
    )

    instagram = st.text_input(
        "Instagram Handle (without @)",
        value=tenant.data.get("instagram_handle", "")
    )

    # ----------------------------------
    # Branding colors (CORRECT PLACE)
    # ----------------------------------
    primary_color = st.color_picker(
        "Primary Brand Color",
        value=tenant.data.get("primary_color", "#000000")
    )

    accent_color = st.color_picker(
        "Accent Brand Color",
        value=tenant.data.get("accent_color", "#444444")
    )

    # ----------------------------------
    # Save settings
    # ----------------------------------
    if st.button("Save Settings"):
        updates = {
            "address": address,
            "contact": contact,
            "instagram_handle": instagram,
            "primary_color": primary_color,
            "accent_color": accent_color
        }

        # ---- Logo upload ----
        if logo:
            logo_path = f"{tenant_id}/logo.png"
            supabase.storage.from_("branding").upload(
                logo_path,
                logo.getvalue()
            )
            updates["logo_url"] = (
                supabase.storage.from_("branding")
                .get_public_url(logo_path)
            )

        # ---- UPI QR upload ----
        if upi_qr:
            qr_path = f"{tenant_id}/upi_qr.png"
            supabase.storage.from_("branding").upload(
                qr_path,
                upi_qr.getvalue()
            )
            updates["upi_qr_url"] = (
                supabase.storage.from_("branding")
                .get_public_url(qr_path)
            )

        supabase.table("tenants") \
            .update(updates) \
            .eq("id", tenant_id) \
            .execute()

        st.success("✅ Settings saved successfully")
