import streamlit as st
from supabase_client import supabase


def products(tenant_id):
    st.title("🧾 Products")

    # ----------------------------------
    # ADD PRODUCT
    # ----------------------------------
    with st.form("add_product"):
        name = st.text_input("Product Name")
        price = st.number_input("Price (₹)", min_value=0.0, step=1.0)
        category = st.text_input("Category")

        submit = st.form_submit_button("➕ Add Product")

    if submit:
        if not name:
            st.error("Product name is required")
            return

        supabase.table("products").insert({
            "tenant_id": tenant_id,
            "name": name,
            "price": float(price),
            "category": category,
            "available": True
        }).execute()

        st.success("Product added successfully")
        st.rerun()

    st.divider()

    # ----------------------------------
    # LIST & EDIT PRODUCTS
    # ----------------------------------
    products = supabase.table("products") \
        .select("*") \
        .eq("tenant_id", tenant_id) \
        .order("category", desc=False) \
        .order("name", desc=False) \
        .execute()

    if not products.data:
        st.info("No products added yet")
        return

    for p in products.data:
        with st.expander(f"{p['name']} — ₹{p['price']}"):
            new_name = st.text_input(
                "Product Name",
                value=p["name"],
                key=f"name_{p['id']}"
            )

            new_price = st.number_input(
                "Price (₹)",
                min_value=0.0,
                value=float(p["price"]),
                step=1.0,
                key=f"price_{p['id']}"
            )

            new_category = st.text_input(
                "Category",
                value=p.get("category", ""),
                key=f"cat_{p['id']}"
            )

            available = st.checkbox(
                "Available",
                value=p.get("available", True),
                key=f"avail_{p['id']}"
            )

            col1, col2 = st.columns(2)

            with col1:
                if st.button("💾 Update", key=f"upd_{p['id']}"):
                    supabase.table("products").update({
                        "name": new_name,
                        "price": float(new_price),
                        "category": new_category,
                        "available": available
                    }).eq("id", p["id"]).execute()

                    st.success("Product updated")
                    st.rerun()

            with col2:
                if st.button("🗑 Delete", key=f"del_{p['id']}"):
                    supabase.table("products") \
                        .delete() \
                        .eq("id", p["id"]) \
                        .execute()

                    st.warning("Product deleted")
                    st.rerun()
