import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Yalidine BI Dashboard",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"   # sidebar starts open; the arrow in the corner opens/closes it
)


# --------------------------------------------------
# CUSTOM STYLE: eye-catching sidebar toggle button
# --------------------------------------------------

st.markdown(
    """
    <style>
    /* Button shown when the sidebar is closed */
    [data-testid="stSidebarCollapsedControl"],
    [data-testid="collapsedControl"] {
        background: linear-gradient(135deg, #ff4b4b, #ff8a4b);
        border-radius: 0 14px 14px 0;
        padding: 8px 10px;
        top: 0.8rem;
        left: 0;
        box-shadow: 0 4px 14px rgba(255, 75, 75, 0.5);
        animation: sidebar-pulse 2s infinite;
        transition: transform 0.2s ease;
    }

    [data-testid="stSidebarCollapsedControl"]:hover,
    [data-testid="collapsedControl"]:hover {
        transform: scale(1.15);
    }

    /* Make the icon white and bigger */
    [data-testid="stSidebarCollapsedControl"] *,
    [data-testid="collapsedControl"] * {
        color: white !important;
        fill: white !important;
        font-size: 1.6rem !important;
    }

    /* Button shown inside the open sidebar to close it */
    [data-testid="stSidebarCollapseButton"] button {
        background: linear-gradient(135deg, #ff4b4b, #ff8a4b);
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(255, 75, 75, 0.4);
    }

    [data-testid="stSidebarCollapseButton"] * {
        color: white !important;
        fill: white !important;
    }

    @keyframes sidebar-pulse {
        0%   { box-shadow: 0 0 0 0 rgba(255, 75, 75, 0.6); }
        70%  { box-shadow: 0 0 0 12px rgba(255, 75, 75, 0); }
        100% { box-shadow: 0 0 0 0 rgba(255, 75, 75, 0); }
    }
    </style>
    """,
    unsafe_allow_html=True
)


# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

@st.cache_data
def load_data():
    connection = sqlite3.connect("ventes.db")

    query = """
    SELECT
        sales.id,
        sales.customer_id,
        customers.name AS customer,
        customers.region AS customer_region,
        products.name AS product,
        products.base_price_5kg,
        products.extra_price_per_kg,
        sales.weight,
        sales.destination,
        sales.delivery_status,
        sales.sale_date
    FROM sales
    JOIN customers ON sales.customer_id = customers.id
    JOIN products ON sales.product_id = products.id
    """

    data = pd.read_sql_query(query, connection)
    connection.close()

    # Revenue: base price up to 5 kg, then extra price per additional kg
    data["revenue"] = data["base_price_5kg"] + (
        (data["weight"] - 5).clip(lower=0) * data["extra_price_per_kg"]
    )

    data["sale_date"] = pd.to_datetime(data["sale_date"])
    data["month"] = data["sale_date"].dt.to_period("M").astype(str)
    data["sale_date_display"] = data["sale_date"].dt.strftime("%Y-%m-%d")

    return data


df = load_data()


# --------------------------------------------------
# SIDEBAR NAVIGATION
# --------------------------------------------------

with st.sidebar:
    st.markdown("## 📦 Yalidine Express")
    st.caption("Business Intelligence")
    st.divider()

    page = st.radio(
        "Navigation",
        ["📊 Dashboard", "📋 Data"],
        label_visibility="collapsed"
    )

    st.divider()
    st.caption(f"{len(df)} sales · Aug – Sep 2026")


# --------------------------------------------------
# PAGE: DATA
# --------------------------------------------------

if page == "📋 Data":

    st.title("📋 Sales Data")
    st.write("Full list of delivery sales.")

    sales_display = df[
        [
            "sale_date_display",
            "id",
            "customer",
            "customer_region",
            "product",
            "weight",
            "destination",
            "delivery_status",
            "revenue",
        ]
    ].sort_values("sale_date_display")

    st.dataframe(
        sales_display,
        use_container_width=True,
        hide_index=True
    )


# --------------------------------------------------
# PAGE: DASHBOARD
# --------------------------------------------------

else:

    st.title("📊 Yalidine Delivery Dashboard")
    st.write("Business Intelligence analysis of delivery sales.")

    # ---------- KPIs ----------

    total_revenue = df["revenue"].sum()
    total_quantity = len(df)

    # Successful delivery rate (Pending excluded)
    delivered = (df["delivery_status"] == "Delivered").sum()
    returned = (df["delivery_status"] == "Returned").sum()
    failed = (df["delivery_status"] == "Failed").sum()
    pending = (df["delivery_status"] == "Pending").sum()

    successful_count = delivered + returned
    total_completed = successful_count + failed
    successful_delivery_rate = (
        successful_count / total_completed * 100 if total_completed > 0 else 0
    )

    # Customer retention rate
    orders_per_customer = df.groupby("customer_id").size()
    total_customers = len(orders_per_customer)
    returning_customers = (orders_per_customer > 1).sum()
    one_time_customers = total_customers - returning_customers
    retention_rate = (
        returning_customers / total_customers * 100 if total_customers > 0 else 0
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        with st.container(border=True):
            st.metric("💰 Total Revenue", f"{total_revenue:,.0f} DA")

    with col2:
        with st.container(border=True):
            st.metric("📦 Total Quantity Sold", total_quantity)

    with col3:
        with st.container(border=True):
            st.metric("✅ Successful Delivery Rate", f"{successful_delivery_rate:.1f}%")

    with col4:
        with st.container(border=True):
            st.metric("🔁 Customer Retention Rate", f"{retention_rate:.1f}%")

    # ---------- Revenue by region + Top products ----------

    left, right = st.columns(2)

    with left:
        with st.container(border=True):
            st.subheader("📊 Revenue by Region")
            revenue_by_region = (
                df.groupby("customer_region")["revenue"]
                .sum()
                .sort_values(ascending=False)
            )
            st.bar_chart(revenue_by_region)

    with right:
        with st.container(border=True):
            st.subheader("🏆 Top Products")
            revenue_by_product = (
                df.groupby("product")["revenue"]
                .sum()
                .sort_values(ascending=False)
            )
            st.bar_chart(revenue_by_product)

    # ---------- Monthly revenue trend ----------

    with st.container(border=True):
        st.subheader("📈 Monthly Revenue Trend")

        monthly_revenue = (
            df.groupby("month")["revenue"]
            .sum()
            .sort_index()
            .reset_index()
        )

        fig = px.line(monthly_revenue, x="month", y="revenue", markers=True)

        fig.update_xaxes(
            tickmode="array",
            tickvals=["2026-08", "2026-09"],
            ticktext=["August", "September"]
        )

        fig.update_yaxes(
            range=[
                monthly_revenue["revenue"].min() * 0.95,
                monthly_revenue["revenue"].max() * 1.05
            ]
        )

        fig.update_layout(xaxis_title="Month", yaxis_title="Revenue (DA)")

        st.plotly_chart(fig, use_container_width=True)

    # ---------- Delivery performance + Customer retention ----------

    left, right = st.columns(2)

    with left:
        with st.container(border=True):
            st.subheader("📦 Delivery Performance")
            delivery_chart = pd.DataFrame({
                "Delivery Result": ["Successfully Delivered", "Not Successful", "Pending"],
                "Count": [successful_count, failed, pending]
            })
            fig_delivery = px.pie(
                delivery_chart,
                names="Delivery Result",
                values="Count",
                hole=0.5,
                color="Delivery Result",
                color_discrete_map={
                    "Successfully Delivered": "#2ecc71",
                    "Not Successful": "#e74c3c",
                    "Pending": "#f1c40f"
                }
            )
            fig_delivery.update_traces(textinfo="percent+value")
            st.plotly_chart(fig_delivery, use_container_width=True)

    with right:
        with st.container(border=True):
            st.subheader("🔁 Customer Retention")
            retention_chart = pd.DataFrame({
                "Customer Type": ["Returning Customers", "One-Time Customers"],
                "Customers": [returning_customers, one_time_customers]
            })
            fig_retention = px.pie(
                retention_chart,
                names="Customer Type",
                values="Customers",
                hole=0.5,
                color="Customer Type",
                color_discrete_map={
                    "Returning Customers": "#3498db",
                    "One-Time Customers": "#f39c12"
                }
            )
            fig_retention.update_traces(textinfo="percent+value")
            st.plotly_chart(fig_retention, use_container_width=True)