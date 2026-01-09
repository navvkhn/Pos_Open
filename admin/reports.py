import streamlit as st
import pandas as pd
from supabase_client import supabase
from datetime import date, datetime
import pytz

IST = pytz.timezone("Asia/Kolkata")


def reports(tenant_id):
    st.title("📊 Business Reports & Insights")

    # --------------------------------------------------
    # 📅 DATE FILTER (IST → UTC SAFE)
    # --------------------------------------------------
    col1, col2 = st.columns(2)

    with col1:
        start_date = st.date_input("From Date", value=date.today())
    with col2:
        end_date = st.date_input("To Date", value=date.today())

    if start_date > end_date:
        st.error("Start date cannot be after end date")
        return

    start_ist = datetime.combine(start_date, datetime.min.time()).astimezone(IST)
    end_ist = datetime.combine(end_date, datetime.max.time()).astimezone(IST)

    start_utc = start_ist.astimezone(pytz.utc).isoformat()
    end_utc = end_ist.astimezone(pytz.utc).isoformat()

    # --------------------------------------------------
    # 🧾 FETCH ORDERS (TENANT SAFE)
    # --------------------------------------------------
    orders = supabase.table("orders") \
        .select("""
            id,
            customer_id,
            customer_name,
            total,
            discount_amount,
            created_at
        """) \
        .eq("tenant_id", tenant_id) \
        .gte("created_at", start_utc) \
        .lte("created_at", end_utc) \
        .execute()

    if not orders.data:
        st.info("No data for selected period")
        return

    orders_df = pd.DataFrame(orders.data)
    orders_df["discount_amount"] = orders_df["discount_amount"].fillna(0)

    # --------------------------------------------------
    # 📊 KPIs
    # --------------------------------------------------
    total_revenue = orders_df["total"].sum()
    total_discount = orders_df["discount_amount"].sum()
    total_orders = len(orders_df)

    avg_order_value = total_revenue / total_orders if total_orders else 0
    avg_discount = total_discount / total_orders if total_orders else 0
    discount_ratio = (
        (total_discount / (total_revenue + total_discount)) * 100
        if total_revenue else 0
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 Revenue (After Discount)", f"₹ {total_revenue:.2f}")
    c2.metric("💸 Total Discount Given", f"₹ {total_discount:.2f}")
    c3.metric("📦 Avg Order Value", f"₹ {avg_order_value:.2f}")
    c4.metric("🏷 Avg Discount / Order", f"₹ {avg_discount:.2f}")

    st.caption(f"📉 Discount = {discount_ratio:.1f}% of gross revenue")
    st.divider()

    # --------------------------------------------------
    # 🧑‍🤝‍🧑 MOST VISITED CUSTOMERS ⭐ NEW
    # --------------------------------------------------
    st.subheader("🧑‍🤝‍🧑 Most Visited Customers")

    customers = supabase.table("customers") \
        .select("id, name, mobile") \
        .eq("tenant_id", tenant_id) \
        .execute()

    customers_df = pd.DataFrame(customers.data)

    if not customers_df.empty:
        customer_summary = (
            orders_df
            .groupby(["customer_id", "customer_name"])
            .agg(
                visits=("id", "count"),
                total_spent=("total", "sum"),
                avg_bill=("total", "mean")
            )
            .reset_index()
            .sort_values(by="visits", ascending=False)
        )

        customer_summary = customer_summary.merge(
            customers_df,
            left_on="customer_id",
            right_on="id",
            how="left"
        )

        customer_summary = customer_summary[[
            "name",
            "mobile",
            "visits",
            "total_spent",
            "avg_bill"
        ]]

        customer_summary.columns = [
            "Customer Name",
            "Mobile",
            "Visits",
            "Total Spent (₹)",
            "Avg Bill (₹)"
        ]

        st.dataframe(
            customer_summary.head(10),
            use_container_width=True
        )
    else:
        st.info("No customer data available")

    st.divider()

    # --------------------------------------------------
    # 🍽 PRODUCT INSIGHTS
    # --------------------------------------------------
    order_ids = orders_df["id"].tolist()

    items = supabase.table("order_items") \
        .select("""
            product_name,
            quantity,
            price,
            orders!inner (
                tenant_id
            )
        """) \
        .in_("order_id", order_ids) \
        .eq("orders.tenant_id", tenant_id) \
        .execute()

    items_df = pd.DataFrame(items.data)

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
    # 📈 DAILY TRENDS
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
    st.line_chart(daily.set_index("date")[["revenue", "discount"]])

    st.subheader("📊 Daily Orders Count")
    st.bar_chart(daily.set_index("date")["orders"])

    st.divider()

    # --------------------------------------------------
    # 📥 EXPORTS
    # --------------------------------------------------
    st.subheader("📥 Export Data")

    c1, c2 = st.columns(2)

    with c1:
        st.download_button(
            "⬇️ Download Orders CSV",
            data=orders_df.to_csv(index=False),
            file_name="orders_report.csv",
            mime="text/csv"
        )

    with c2:
        st.download_button(
            "⬇️ Download Product Sales CSV",
            data=product_summary.to_csv(index=False),
            file_name="product_sales_report.csv",
            mime="text/csv"
        )
