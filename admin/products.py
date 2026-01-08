import streamlit as st
from supabase_client import supabase

def products(tenant_id):
    st.title("🧾 Products")

    # -----------------------------
    # Add product form
    # -----------------------------
    with st.form("add_product"):
        name = st.text_input("Product Name")
        price = st.number_input("Price", min_value=0.0)
        category = st.text_input("Category")
        image = st.file_uploader("Product Image", type=["jpg", "png"])
        submit = st.form_submit_button("Add Product")

        if submit:
            if not name or price <= 0:
                st.error("Name and price are required")
                return

            image_url = None

            # Upload image if provided
            if image:
                path = f"{tenant_id}/{name.replace(' ', '_')}_{image.name}"

                supabase.storage.from_("product-images").upload(
                    path,
                    image.getvalue(),
                    {"content-type": image.type}
                )

                image_url = supabase.storage.from_("product-images") \
                    .get_public_url(path)

            # Insert product
            supabase.table("products").insert({
                "tenant_id": tenant_id,
                "name": name,
                "price": price,
                "category": category,
                "image_url": image_url
            }).execute()

            st.success("✅ Product added")
            st.rerun()

    # -----------------------------
    # Show products
    # -----------------------------
    data = supabase.table("products") \
        .select("*") \
        .eq("tenant_id", tenant_id) \
        .execute()

    st.subheader("📋 Product List")

    for p in data.data:
        cols = st.columns([1, 3, 1])

        if p.get("image_url"):
            cols[0].image(p["image_url"], width=80)

        cols[1].write(f"**{p['name']}**")
        cols[2].write(f"₹{p['price']}")
