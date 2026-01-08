import streamlit as st
from supabase_client import supabase

def customer_menu(tenant_name: str):
    st.title(f"🍽 Menu – {tenant_name}")

    # Get tenant
    tenant_res = supabase.table("tenants") \
        .select("id") \
        .eq("name", tenant_name) \
        .execute()

    if not tenant_res.data:
        st.error("Restaurant not found")
        return

    tenant_id = tenant_res.data[0]["id"]

    table_no = st.text_input("Table Number")

    products = supabase.table("products") \
        .select("*") \
        .eq("tenant_id", tenant_id) \
        .eq("available", True) \
        .execute()

    if not products.data:
        st.info("Menu not available")
        return

    cart = st.session_state.get("cart", {})

    st.subheader("Menu")

    for p in products.data:
        qty = st.number_input(
            f"{p['name']} – ₹{p['price']}",
            min_value=0,
            key=f"cust_{p['id']}"
        )
        if qty > 0:
            cart[p["id"]] = {
                "name": p["name"],
                "qty": qty,
                "price": p["price"]
            }

    st.session_state["cart"] = cart

    if st.button("🛒 Place Order"):
        if not cart:
            st.warning("Cart is empty")
            return

        order = supabase.table("orders").insert({
            "tenant_id": tenant_id,
            "table_no": table_no,
            "total": sum(
                item["qty"] * item["price"]
                for item in cart.values()
            ),
            "status": "open"
        }).execute()

        order_id = order.data[0]["id"]

        for item in cart.values():
            supabase.table("order_items").insert({
                "order_id": order_id,
                "product_name": item["name"],
                "quantity": item["qty"],
                "price": item["qty"] * item["price"]
            }).execute()

        st.success("✅ Order placed successfully")
        st.session_state["cart"] = {}
        st.rerun()
