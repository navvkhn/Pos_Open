import streamlit as st
import pandas as pd
from supabase_client import supabase
from datetime import date


def reports(tenant_id):
    st.title("📊 Business Reports & Insights")

    # --------------------------------------------------
    # Date Filter
    # --------------------------------------------------
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("From Date", value=date.today())
    with col2:
        end_date = st.date_input("To Date", value=date.today())

    if start_date > end_date:
        st.error("Start date cannot be after end date")
        return

    # --------------------------------------------------
    # Fetch orders
    # --------------------------------------------------
    orders = supabase.table("orders") \
        .select("*") \
        .eq("tenant_id", tenant_id) \
        .gte("created_at", f"{start_date}T00:00:00") \
        .lte("created_at", f"{end_date}T23:59:59") \
        .execute()

    if not orders.data:
        st.info("No data for selected period")
        return

    orders_df = pd.DataFrame(orders.data)

    # Fill null discounts
    orders_df["discount_amount"] = orders_df["discount_amount"].fillna(0)

    # --------------------------------------------------
    # KPIs
    # --------------------------------------------------
    total_revenue = orders_df["total"].sum()
    total_discount = orders_df["discount_amount"].sum()
    total_orders = len(orders_df)
    avg_order_value = total_revenue / total_orders if total_orders else 0
    avg_discount = total_discount / total_orders if total_orders else 0
    discount_ratio = (total_discount / (total_revenue + total_discount)) * 100 if total_revenue else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("💰 Revenue (After Discount)", f"₹ {total_revenue:.2f}")
    col2.metric("💸 Total Discount Given", f"₹ {total_discount:.2f}")
    col3.metric("📦 Avg Order Value", f"₹ {avg_order_value:.2f}")
    col4.metric("🏷 Avg Discount / Order", f"₹ {avg_discount:.2f}")

    st.caption(f"📉 Discount = {discount_ratio:.1f}% of gross revenue")

    st.divider()

    # --------------------------------------------------
    # Discount vs No Discount
    # --------------------------------------------------
    discount_orders = orders_df[orders_df["discount_amount"] > 0]
    no_discount_orders = orders_df[orders_df["discount_amount"] == 0]

    col1, col2 = st.columns(2)
    col1.metric("🟢 Orders with Discount", len(discount_orders))
    col2.metric("⚪ Orders without Discount", len(no_discount_orders))

    st.divider()

    # --------------------------------------------------
    # Fetch order items
    # --------------------------------------------------
    order_ids = orders_df["id"].tolist()

    items = supabase.table("order_items") \
        .select("*") \
        .in_("order_id", order_ids) \
        .execute()

    items_df = pd.DataFrame(items.data)

    # --------------------------------------------------
    # Product Insights
    # --------------------------------------------------
    product_summary = (
        items_df
        .groupby("product_name")
        .agg(
            quantity_sold=("quantity", "sum"),
            revenue=("price", "sum")
        )
        .reset_index()
        .sort_values(by="quantity_sold", ascending=False)
    )

    st.subheader("🏆 Top Products")
    st.dataframe(product_summary.head(10), use_container_width=True)

    st.divider()

    # --------------------------------------------------
    # Daily Revenue & Discount Trend
    # --------------------------------------------------
    orders_df["date"] = pd.to_datetime(orders_df["created_at"]).dt.date

    daily = (
        orders_df
        .groupby("date")
        .agg(
            revenue=("total", "sum"),
            discount=("discount_amount", "sum"),
            orders=("id", "count")
        )
        .reset_index()
    )

    st.subheader("📈 Daily Revenue vs Discount")
    st.line_chart(
        daily.set_index("date")[["revenue", "discount"]]
    )

    st.subheader("📊 Daily Orders Count")
    st.bar_chart(daily.set_index("date")["orders"])

    st.divider()

    # --------------------------------------------------
    # CSV Export (WITH DISCOUNTS)
    # --------------------------------------------------
    st.subheader("📥 Export Data")

    col1, col2 = st.columns(2)

    with col1:
        st.download_button(
            "⬇️ Download Orders CSV",
            data=orders_df.to_csv(index=False),
            file_name="orders_with_discounts.csv",
            mime="text/csv"
        )

    with col2:
        st.download_button(
            "⬇️ Download Product Sales CSV",
            data=product_summary.to_csv(index=False),
            file_name="product_sales_report.csv",
            mime="text/csv"
        )
