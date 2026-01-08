import streamlit as st
from supabase_client import supabase

def products(tenant_id):
    st.title("🧾 Products")

    # =====================================================
    # ADD PRODUCT
    # =====================================================
    with st.form("add_product"):
        st.subheader("➕ Add Product")

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

            if image:
                path = f"{tenant_id}/{name.replace(' ', '_')}_{image.name}"
                supabase.storage.from_("product-images").upload(
                    path,
                    image.getvalue(),
                    {"content-type": image.type}
                )
                image_url = supabase.storage.from_("product-images").get_public_url(path)

            supabase.table("products").insert({
                "tenant_id": tenant_id,
                "name": name,
                "price": price,
                "category": category,
                "image_url": image_url,
                "available": True
            }).execute()

            st.success("✅ Product added")
            st.rerun()

    st.divider()

    # =====================================================
    # EDIT PRODUCTS
    # =====================================================
    st.subheader("✏️ Edit Products")

    products = supabase.table("products") \
        .select("*") \
        .eq("tenant_id", tenant_id) \
        .order("created_at", desc=True) \
        .execute()

    if not products.data:
        st.info("No products added yet")
        return

    for p in products.data:
        with st.expander(f"{p['name']} — ₹{p['price']}"):
            cols = st.columns([1, 3])

            # ---- IMAGE ----
            if p.get("image_url"):
                cols[0].image(p["image_url"], width=120)

            # ---- EDIT FORM ----
            with cols[1]:
                new_name = st.text_input(
                    "Name", value=p["name"], key=f"name_{p['id']}"
                )
                new_price = st.number_input(
                    "Price", value=float(p["price"]), min_value=0.0,
                    key=f"price_{p['id']}"
                )
                new_category = st.text_input(
                    "Category", value=p.get("category", ""),
                    key=f"cat_{p['id']}"
                )
                available = st.checkbox(
                    "Available", value=p["available"],
                    key=f"avail_{p['id']}"
                )

                new_image = st.file_uploader(
                    "Replace Image",
                    type=["jpg", "png"],
                    key=f"img_{p['id']}"
                )

                if st.button("💾 Save Changes", key=f"save_{p['id']}"):
                    image_url = p.get("image_url")

                    if new_image:
                        path = f"{tenant_id}/{new_name.replace(' ', '_')}_{new_image.name}"
                        supabase.storage.from_("product-images").upload(
                            path,
                            new_image.getvalue(),
                            {"content-type": new_image.type},
                            upsert=True
                        )
                        image_url = supabase.storage.from_("product-images").get_public_url(path)

                    supabase.table("products").update({
                        "name": new_name,
                        "price": new_price,
                        "category": new_category,
                        "available": available,
                        "image_url": image_url
                    }).eq("id", p["id"]).execute()

                    st.success("✅ Updated")
                    st.rerun()
