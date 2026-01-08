import streamlit as st
from supabase_client import supabase

def products(tenant_id):
    st.title("🧾 Products")

    with st.form("add_product"):
        name = st.text_input("Product Name")
        price = st.number_input("Price", min_value=0.0)
        category = st.text_input("Category")
        submit = st.form_submit_button("Add")
image = st.file_uploader("Product Image", type=["jpg", "png"])

if image:
    file = supabase.storage.from_("product-images").upload(
        f"{tenant_id}/{image.name}",
        image.getvalue(),
        {"content-type": image.type}
    )
    image_url = supabase.storage.from_("product-images").get_public_url(
        f"{tenant_id}/{image.name}"
    )

        if submit:
            supabase.table("products").insert({
                "tenant_id": tenant_id,
                "name": name,
                "price": price,
                "category": category
            }).execute()
            st.success("Product added")
            st.rerun()

    data = supabase.table("products") \
        .select("*") \
        .eq("tenant_id", tenant_id) \
        .execute()

    for p in data.data:
        st.write(f"{p['name']} — ₹{p['price']}")
