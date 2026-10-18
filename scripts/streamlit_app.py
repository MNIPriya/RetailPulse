
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# --------------------------------------------------
# 1. APP CONFIGURATION
# --------------------------------------------------

PROJECT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_DIR / "outputs"

st.set_page_config(
    page_title="RetailPulse | Retail Analytics",
    page_icon="📊",
    layout="wide",
)

st.title("📊 RetailPulse")
st.caption("Retail Analytics | Sales, Customers, Forecasts & Inventory")


# --------------------------------------------------
# 2. LOAD PROJECT OUTPUTS
# --------------------------------------------------

@st.cache_data
def load_csv(filename):
    path = OUTPUT_DIR / filename

    if not path.exists():
        return pd.DataFrame()

    return pd.read_csv(path)


sales = load_csv("day13_daily_sales_summary.csv")
segments = load_csv("day3_customer_segments.csv")
forecast = load_csv("day8_ensemble_forecast.csv")
churn = load_csv("day9_churn_predictions.csv")
inventory = load_csv("day10_inventory_recommendations.csv")


# --------------------------------------------------
# 3. VALIDATE AND PREPARE DATA
# --------------------------------------------------

if sales.empty:
    st.error(
        "Daily sales data could not be loaded. "
        "Check outputs/day13_daily_sales_summary.csv."
    )
    st.stop()

sales["Date"] = pd.to_datetime(sales["Date"], errors="coerce")
sales = sales.dropna(subset=["Date"]).sort_values("Date")

for column in ["TotalRevenue", "TotalUnits", "TotalInvoices"]:
    sales[column] = pd.to_numeric(
        sales[column], errors="coerce"
    ).fillna(0)

if not segments.empty:
    segments["CustomerID"] = segments["CustomerID"].astype(str)

if not forecast.empty:
    forecast["Date"] = pd.to_datetime(
        forecast["Date"], errors="coerce"
    )
    forecast = forecast.dropna(subset=["Date"]).sort_values("Date")

if not churn.empty and "ChurnRiskProbability" in churn.columns:
    churn["ChurnRiskProbability"] = pd.to_numeric(
        churn["ChurnRiskProbability"], errors="coerce"
    )

if not inventory.empty:
    for column in [
        "SimulatedStockOnHand",
        "ReorderPoint",
        "TargetStockLevel",
        "RecommendedOrderQuantity",
        "AverageDailyDemand",
    ]:
        if column in inventory.columns:
            inventory[column] = pd.to_numeric(
                inventory[column], errors="coerce"
            )


# --------------------------------------------------
# 4. SIDEBAR NAVIGATION
# --------------------------------------------------

st.sidebar.title("📊 RetailPulse")
st.sidebar.caption("Retail Analytics Dashboard")
st.sidebar.divider()

selected_section = st.sidebar.radio(
    "Navigate to",
    [
        "Overview",
        "Forecasting",
        "Customer Segmentation",
        "Churn Analysis",
        "Inventory",
    ],
    key="dashboard_navigation",
)

st.sidebar.divider()
st.sidebar.header("Dashboard Filters")


# Date filter
min_date = sales["Date"].min().date()
max_date = sales["Date"].max().date()

selected_dates = st.sidebar.date_input(
    "Sales date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
    key="sales_date_range",
)

if isinstance(selected_dates, (tuple, list)):
    if len(selected_dates) == 2:
        start_date, end_date = selected_dates
    elif len(selected_dates) == 1:
        start_date = end_date = selected_dates[0]
    else:
        start_date, end_date = min_date, max_date
else:
    start_date = end_date = selected_dates

filtered_sales = sales[
    (sales["Date"].dt.date >= start_date)
    & (sales["Date"].dt.date <= end_date)
].copy()

# --------------------------------------------------
# DOWNLOAD REPORTS DROPDOWN
# --------------------------------------------------

with st.popover("⬇ Download Reports"):

    st.markdown("### Export your reports")

    st.download_button(
        label="📊 Download Sales CSV",
        data=filtered_sales.to_csv(index=False).encode("utf-8"),
        file_name="retailpulse_sales_report.csv",
        mime="text/csv",
        key="header_sales_csv",
        use_container_width=True,
    )

    if not inventory.empty:
        st.download_button(
            label="📦 Download Inventory CSV",
            data=inventory.to_csv(index=False).encode("utf-8"),
            file_name="retailpulse_inventory_report.csv",
            mime="text/csv",
            key="header_inventory_csv",
            use_container_width=True,
        )

    st.divider()

    if st.button("📄 Generate PDF Summary", key="header_generate_pdf"):

        pdf_buffer = BytesIO()
        pdf = SimpleDocTemplate(
            pdf_buffer,
            pagesize=landscape(A4),
        )

        styles = getSampleStyleSheet()

        story = [
            Paragraph(
                "RetailPulse Business Summary",
                styles["Title"],
            ),
            Spacer(1, 12),
            Paragraph(
                f"Total Revenue: {filtered_sales['TotalRevenue'].sum():,.2f}",
                styles["Normal"],
            ),
            Paragraph(
                f"Total Units Sold: {filtered_sales['TotalUnits'].sum():,.0f}",
                styles["Normal"],
            ),
            Paragraph(
                f"Total Invoices: {filtered_sales['TotalInvoices'].sum():,.0f}",
                styles["Normal"],
            ),
            Spacer(1, 12),
            Paragraph(
                "Note: Churn scores are proxy predictions, "
                "and inventory levels are simulated.",
                styles["Italic"],
            ),
        ]

        pdf.build(story)
        st.session_state["retailpulse_pdf"] = pdf_buffer.getvalue()

    if "retailpulse_pdf" in st.session_state:
        st.download_button(
            label="⬇ Download Business PDF",
            data=st.session_state["retailpulse_pdf"],
            file_name="retailpulse_business_summary.pdf",
            mime="application/pdf",
            key="header_download_pdf",
            use_container_width=True,
        )


# Section-specific sidebar controls
scenario_pct = 10
selected_cluster = None
risk_threshold = 0.50
selected_statuses = []
search_product = ""

if selected_section == "Forecasting":
    st.sidebar.subheader("Forecast Controls")

    scenario_pct = st.sidebar.slider(
        "Assumed revenue change (%)",
        min_value=-30,
        max_value=50,
        value=10,
        step=5,
        help="Adjust the saved ensemble forecast for a hypothetical scenario.",
        key="sidebar_revenue_scenario",
    )

if selected_section == "Customer Segmentation":
    st.sidebar.subheader("Customer Controls")

    if (
        not segments.empty
        and "KMeans_Cluster" in segments.columns
    ):
        cluster_options = sorted(
            segments["KMeans_Cluster"].dropna().unique().tolist()
        )

        if cluster_options:
            selected_cluster = st.sidebar.selectbox(
                "Select customer cluster",
                options=cluster_options,
                format_func=lambda x: f"Cluster {x}",
                key="sidebar_customer_cluster",
            )

if selected_section == "Churn Analysis":
    st.sidebar.subheader("Churn Controls")

    risk_threshold = st.sidebar.slider(
        "Churn risk threshold",
        min_value=0.0,
        max_value=1.0,
        value=0.50,
        step=0.05,
        format="%.2f",
        help="Adjust which records are flagged for further review.",
        key="sidebar_churn_threshold",
    )

if selected_section == "Inventory":
    st.sidebar.subheader("Inventory Controls")

    if (
        not inventory.empty
        and "InventoryStatus" in inventory.columns
    ):
        statuses = sorted(
            inventory["InventoryStatus"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        selected_statuses = st.sidebar.multiselect(
            "Inventory status",
            options=statuses,
            default=statuses,
            key="sidebar_inventory_status",
        )

    search_product = st.sidebar.text_input(
        "Search product",
        placeholder="Product code or description",
        key="sidebar_product_search",
    )


# --------------------------------------------------
# 5. OVERVIEW
# --------------------------------------------------

if selected_section == "Overview":

    st.header("Sales Overview")

    st.caption(
        "Review sales performance for your selected date range."
    )

    total_revenue = filtered_sales["TotalRevenue"].sum()
    total_units = filtered_sales["TotalUnits"].sum()
    total_invoices = filtered_sales["TotalInvoices"].sum()

    unique_customers = (
        segments["CustomerID"].nunique()
        if not segments.empty and "CustomerID" in segments.columns
        else 0
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Revenue", f"{total_revenue:,.2f}")
    col2.metric("Total Invoices", f"{total_invoices:,.0f}")
    col3.metric("Units Sold", f"{total_units:,.0f}")
    col4.metric("Unique Customers", f"{unique_customers:,.0f}")

    st.caption(
        f"Sales period: {start_date} to {end_date}."
    )

    st.divider()
    st.subheader("Daily Revenue Trends")

    if filtered_sales.empty:
        st.info("No sales records are available for this date range.")
    else:
        revenue_chart = px.line(
            filtered_sales,
            x="Date",
            y="TotalRevenue",
            title="Daily Revenue Over Time",
            markers=True,
            labels={
                "Date": "Date",
                "TotalRevenue": "Revenue",
            },
        )

        revenue_chart.update_layout(
            hovermode="x unified",
            xaxis_title="Date",
            yaxis_title="Revenue",
        )

        st.plotly_chart(
            revenue_chart,
            use_container_width=True,
        )

        monthly_sales = (
            filtered_sales.assign(
                Month=filtered_sales["Date"].dt.to_period("M").astype(str)
            )
            .groupby("Month", as_index=False)["TotalRevenue"]
            .sum()
        )

        monthly_chart = px.bar(
            monthly_sales,
            x="Month",
            y="TotalRevenue",
            title="Monthly Revenue",
            labels={
                "Month": "Month",
                "TotalRevenue": "Revenue",
            },
        )

        st.plotly_chart(
            monthly_chart,
            use_container_width=True,
        )


# --------------------------------------------------
# 6. FORECASTING
# --------------------------------------------------

elif selected_section == "Forecasting":

    st.header("Revenue Forecasting")

    st.write(
        "Compare the saved Prophet, LSTM, and ensemble forecasts, "
        "then explore a hypothetical revenue scenario."
    )

    if forecast.empty:
        st.warning("Forecast data is unavailable.")
    else:
        required_forecast_columns = [
            "Date",
            "ActualRevenue",
            "Prophet_Forecast",
            "LSTM_Forecast",
            "Ensemble_Forecast",
        ]

        if all(
            col in forecast.columns
            for col in required_forecast_columns
        ):
            fig = go.Figure()

            fig.add_trace(
                go.Scatter(
                    x=forecast["Date"],
                    y=forecast["ActualRevenue"],
                    mode="lines+markers",
                    name="Actual Revenue",
                )
            )

            fig.add_trace(
                go.Scatter(
                    x=forecast["Date"],
                    y=forecast["Prophet_Forecast"],
                    mode="lines",
                    name="Prophet",
                )
            )

            fig.add_trace(
                go.Scatter(
                    x=forecast["Date"],
                    y=forecast["LSTM_Forecast"],
                    mode="lines",
                    name="LSTM",
                )
            )

            fig.add_trace(
                go.Scatter(
                    x=forecast["Date"],
                    y=forecast["Ensemble_Forecast"],
                    mode="lines",
                    name="Ensemble",
                )
            )

            fig.update_layout(
                title="Actual Revenue vs Model Forecasts",
                xaxis_title="Date",
                yaxis_title="Revenue",
                hovermode="x unified",
            )

            st.plotly_chart(fig, use_container_width=True)

            st.caption(
                "These are saved test-period forecasts, not live "
                "future predictions."
            )
        else:
            st.warning(
                "The forecast file is missing expected columns."
            )

    st.divider()
    st.subheader("Revenue What-If Analysis")

    st.write(
        "Use the revenue-change slider in the sidebar to explore "
        "a hypothetical increase or decrease."
    )

    required_columns = [
        "Date",
        "Ensemble_Forecast",
        "ActualRevenue",
    ]

    if (
        not forecast.empty
        and all(col in forecast.columns for col in required_columns)
    ):
        scenario = forecast.copy()

        scenario["ScenarioRevenue"] = (
            scenario["Ensemble_Forecast"]
            * (1 + scenario_pct / 100)
        )

        baseline_total = scenario["Ensemble_Forecast"].sum()
        scenario_total = scenario["ScenarioRevenue"].sum()
        revenue_difference = scenario_total - baseline_total

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Baseline Forecast Revenue",
            f"{baseline_total:,.2f}",
        )

        col2.metric(
            "Scenario Revenue",
            f"{scenario_total:,.2f}",
            delta=f"{revenue_difference:+,.2f}",
        )

        col3.metric(
            "Assumed Change",
            f"{scenario_pct:+d}%",
        )

        fig_scenario = go.Figure()

        fig_scenario.add_trace(
            go.Scatter(
                x=scenario["Date"],
                y=scenario["Ensemble_Forecast"],
                mode="lines+markers",
                name="Baseline Ensemble Forecast",
            )
        )

        fig_scenario.add_trace(
            go.Scatter(
                x=scenario["Date"],
                y=scenario["ScenarioRevenue"],
                mode="lines+markers",
                name="What-If Scenario",
            )
        )

        fig_scenario.add_trace(
            go.Scatter(
                x=scenario["Date"],
                y=scenario["ActualRevenue"],
                mode="lines",
                name="Actual Revenue",
            )
        )

        fig_scenario.update_layout(
            title="Baseline vs What-If Revenue Scenario",
            xaxis_title="Date",
            yaxis_title="Revenue",
            hovermode="x unified",
        )

        st.plotly_chart(
            fig_scenario,
            use_container_width=True,
        )

        st.caption(
            "Scenario revenue is a hypothetical sensitivity analysis "
            "based on saved forecasts. It is not a new model prediction."
        )
    else:
        st.warning(
            "What-if analysis requires Date, Ensemble_Forecast, "
            "and ActualRevenue."
        )


# --------------------------------------------------
# 7. CUSTOMER SEGMENTATION
# --------------------------------------------------

elif selected_section == "Customer Segmentation":

    st.header("Customer Segmentation & Insights")

    if segments.empty or "KMeans_Cluster" not in segments.columns:
        st.warning("Customer segmentation data is unavailable.")
    else:
        cluster_counts = (
            segments.groupby("KMeans_Cluster")
            .size()
            .reset_index(name="CustomerCount")
        )

        cluster_counts["KMeans_Cluster"] = (
            cluster_counts["KMeans_Cluster"].astype(str)
        )

        cluster_chart = px.bar(
            cluster_counts,
            x="KMeans_Cluster",
            y="CustomerCount",
            title="Customers in Each K-Means Cluster",
            labels={
                "KMeans_Cluster": "Cluster",
                "CustomerCount": "Customers",
            },
            text="CustomerCount",
        )

        st.plotly_chart(
            cluster_chart,
            use_container_width=True,
        )

        st.divider()
        st.subheader("Customer Cluster Explorer")

        if selected_cluster is not None:
            selected_customers = segments[
                segments["KMeans_Cluster"] == selected_cluster
            ]

            metric_cols = st.columns(3)

            metric_cols[0].metric(
                "Customers in Cluster",
                f"{len(selected_customers):,}",
            )

            metric_cols[1].metric(
                "Average Customer Spend",
                f"{selected_customers['Monetary'].mean():,.2f}",
            )

            metric_cols[2].metric(
                "Average Recency (days)",
                f"{selected_customers['Recency'].mean():,.1f}",
            )

            st.dataframe(
                selected_customers.head(100),
                use_container_width=True,
                hide_index=True,
            )

        st.divider()
        st.subheader("Customer Behavior Explorer")

        plot_segments = segments.copy()
        plot_segments["KMeans_Cluster"] = (
            plot_segments["KMeans_Cluster"].astype(str)
        )

        segment_fig = px.scatter(
            plot_segments,
            x="Recency",
            y="Monetary",
            color="KMeans_Cluster",
            size="Frequency",
            hover_data=["CustomerID", "Frequency"],
            log_y=True,
            title="Recency vs Monetary Value",
            labels={
                "Recency": "Days Since Last Purchase",
                "Monetary": "Customer Monetary Value",
                "KMeans_Cluster": "Customer Cluster",
                "Frequency": "Purchase Frequency",
            },
        )

        st.plotly_chart(
            segment_fig,
            use_container_width=True,
        )

        segment_profile = (
            segments.groupby("KMeans_Cluster")
            .agg(
                Customers=("CustomerID", "nunique"),
                AverageRecency=("Recency", "mean"),
                AverageFrequency=("Frequency", "mean"),
                AverageMonetary=("Monetary", "mean"),
            )
            .reset_index()
        )

        st.subheader("Customer Segment Summary")

        st.dataframe(
            segment_profile.round(2),
            use_container_width=True,
            hide_index=True,
        )

        st.caption(
            "Lower recency generally means a more recent purchase. "
            "Cluster numbers are model-generated groups, not ranked grades."
        )


# --------------------------------------------------
# 8. CHURN ANALYSIS
# --------------------------------------------------

elif selected_section == "Churn Analysis":

    st.header("Customer Churn-Risk Analysis")

    st.caption(
        "These results use proxy churn labels based on purchasing "
        "inactivity, not confirmed real-world customer churn."
    )

    if (
        churn.empty
        or "ChurnRiskProbability" not in churn.columns
    ):
        st.warning("Churn prediction data is unavailable.")
    else:
        valid_churn = churn.dropna(
            subset=["ChurnRiskProbability"]
        ).copy()

        valid_churn["RiskGroup"] = valid_churn[
            "ChurnRiskProbability"
        ].apply(
            lambda p: (
                f"Higher risk (>= {risk_threshold:.2f})"
                if p >= risk_threshold
                else f"Lower risk (< {risk_threshold:.2f})"
            )
        )

        flagged_records = valid_churn[
            valid_churn["ChurnRiskProbability"] >= risk_threshold
        ].copy()

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Records Scored",
            f"{len(valid_churn):,}",
        )

        col2.metric(
            "Average Risk Probability",
            f"{valid_churn['ChurnRiskProbability'].mean():.1%}",
        )

        col3.metric(
            "Records Above Threshold",
            f"{len(flagged_records):,}",
        )

        risk_counts = (
            valid_churn["RiskGroup"]
            .value_counts()
            .rename_axis("RiskGroup")
            .reset_index(name="Records")
        )

        risk_chart = px.pie(
            risk_counts,
            names="RiskGroup",
            values="Records",
            title="Risk Group Distribution",
        )

        st.plotly_chart(
            risk_chart,
            use_container_width=True,
        )

        st.divider()
        st.subheader("Churn Risk Probability Distribution")

        risk_histogram = px.histogram(
            valid_churn,
            x="ChurnRiskProbability",
            nbins=20,
            title="Predicted Churn-Risk Probabilities",
            labels={
                "ChurnRiskProbability": "Predicted Risk Probability",
                "count": "Number of Records",
            },
        )

        risk_histogram.add_vline(
            x=risk_threshold,
            line_dash="dash",
            annotation_text="Selected threshold",
        )

        st.plotly_chart(
            risk_histogram,
            use_container_width=True,
        )

        st.divider()
        st.subheader("Records Flagged for Review")

        display_columns = [
            column
            for column in [
                "Recency",
                "Frequency",
                "Monetary",
                "ChurnRiskProbability",
                "PredictedChurnProxy",
                "ActualChurnProxy",
            ]
            if column in flagged_records.columns
        ]

        if flagged_records.empty:
            st.info(
                "No records meet the selected risk threshold."
            )
        else:
            st.dataframe(
                flagged_records.sort_values(
                    "ChurnRiskProbability",
                    ascending=False,
                )[display_columns].head(100),
                use_container_width=True,
                hide_index=True,
            )

        st.caption(
            "The risk threshold is an adjustable dashboard setting, "
            "not a validated business cutoff. The prediction file "
            "does not contain customer IDs, so records cannot be "
            "linked to named customers using this file."
        )


# --------------------------------------------------
# 9. INVENTORY
# --------------------------------------------------

elif selected_section == "Inventory":

    st.header("Inventory Recommendations")

    if inventory.empty:
        st.warning("Inventory recommendation data is unavailable.")
    else:
        inventory_view = inventory.copy()

        # Apply sidebar status filter
        if "InventoryStatus" in inventory_view.columns:
            inventory_view = inventory_view[
                inventory_view["InventoryStatus"]
                .astype(str)
                .isin(selected_statuses)
            ]

        # Apply sidebar product search
        if search_product.strip():
            search_term = search_product.strip()

            code_match = (
                inventory_view["ProductCode"]
                .astype(str)
                .str.contains(
                    search_term, case=False, na=False
                )
                if "ProductCode" in inventory_view.columns
                else pd.Series(
                    False, index=inventory_view.index
                )
            )

            description_match = (
                inventory_view["ProductDescription"]
                .astype(str)
                .str.contains(
                    search_term, case=False, na=False
                )
                if "ProductDescription" in inventory_view.columns
                else pd.Series(
                    False, index=inventory_view.index
                )
            )

            inventory_view = inventory_view[
                code_match | description_match
            ]

        st.write(
            "Review inventory recommendations and prioritize "
            "products for replenishment."
        )

        # Inventory overview charts use the filtered data
        if not inventory_view.empty:
            if "InventoryStatus" in inventory_view.columns:
                status_counts = (
                    inventory_view["InventoryStatus"]
                    .fillna("Unknown")
                    .value_counts()
                    .rename_axis("InventoryStatus")
                    .reset_index(name="ProductCount")
                )

                status_chart = px.bar(
                    status_counts,
                    x="InventoryStatus",
                    y="ProductCount",
                    title="Products by Inventory Status",
                    labels={
                        "InventoryStatus": "Status",
                        "ProductCount": "Products",
                    },
                    text="ProductCount",
                )

                st.plotly_chart(
                    status_chart,
                    use_container_width=True,
                )

            if "RecommendedOrderQuantity" in inventory_view.columns:
                top_orders = inventory_view.sort_values(
                    "RecommendedOrderQuantity",
                    ascending=False,
                    na_position="last",
                ).head(15)

                order_chart = px.bar(
                    top_orders,
                    x="ProductCode",
                    y="RecommendedOrderQuantity",
                    hover_data=[
                        column
                        for column in [
                            "ProductDescription",
                            "InventoryStatus",
                        ]
                        if column in top_orders.columns
                    ],
                    title="Top Products by Recommended Order Quantity",
                    labels={
                        "ProductCode": "Product Code",
                        "RecommendedOrderQuantity": "Recommended Order Quantity",
                    },
                )

                st.plotly_chart(
                    order_chart,
                    use_container_width=True,
                )

        st.divider()
        st.subheader("Inventory Decision Center")

        total_products = len(inventory_view)

        reorder_products = (
            inventory_view["InventoryStatus"]
            .astype(str)
            .str.contains("reorder", case=False, na=False)
            .sum()
            if "InventoryStatus" in inventory_view.columns
            else 0
        )

        suggested_units = (
            inventory_view["RecommendedOrderQuantity"]
            .fillna(0)
            .clip(lower=0)
            .sum()
            if "RecommendedOrderQuantity" in inventory_view.columns
            else 0
        )

        metric1, metric2, metric3 = st.columns(3)

        metric1.metric(
            "Products Shown",
            f"{total_products:,}",
        )

        metric2.metric(
            "Products Marked Reorder",
            f"{reorder_products:,}",
        )

        metric3.metric(
            "Suggested Order Units",
            f"{suggested_units:,.0f}",
        )

        preferred_columns = [
            "ProductCode",
            "ProductDescription",
            "InventoryStatus",
            "SimulatedStockOnHand",
            "AverageDailyDemand",
            "ReorderPoint",
            "TargetStockLevel",
            "RecommendedOrderQuantity",
        ]

        available_columns = [
            column
            for column in preferred_columns
            if column in inventory_view.columns
        ]

        st.subheader("Product-Level Recommendations")

        if inventory_view.empty:
            st.info(
                "No products match the selected sidebar filters."
            )
        else:
            if "RecommendedOrderQuantity" in inventory_view.columns:
                inventory_view = inventory_view.sort_values(
                    "RecommendedOrderQuantity",
                    ascending=False,
                    na_position="last",
                )

            st.dataframe(
                inventory_view[available_columns],
                use_container_width=True,
                hide_index=True,
            )

            chart_columns = [
                "SimulatedStockOnHand",
                "ReorderPoint",
            ]

            if all(
                column in inventory_view.columns
                for column in chart_columns
            ):
                plot_data = inventory_view.dropna(
                    subset=chart_columns
                )

                if not plot_data.empty:
                    fig_inventory = px.scatter(
                        plot_data,
                        x="ReorderPoint",
                        y="SimulatedStockOnHand",
                        color=(
                            "InventoryStatus"
                            if "InventoryStatus" in plot_data.columns
                            else None
                        ),
                        hover_name=(
                            "ProductDescription"
                            if "ProductDescription" in plot_data.columns
                            else None
                        ),
                        hover_data=[
                            column
                            for column in [
                                "ProductCode",
                                "RecommendedOrderQuantity",
                                "AverageDailyDemand",
                            ]
                            if column in plot_data.columns
                        ],
                        title="Estimated Stock vs Reorder Point",
                        labels={
                            "ReorderPoint": "Estimated Reorder Point",
                            "SimulatedStockOnHand": "Simulated Stock on Hand",
                            "InventoryStatus": "Recommendation Status",
                        },
                    )

                    st.plotly_chart(
                        fig_inventory,
                        use_container_width=True,
                    )

        st.caption(
            "Inventory quantities and stock-on-hand values are simulated "
            "estimates based on assumed inventory conditions. Validate "
            "against actual stock and supplier lead times before ordering."
        )


# --------------------------------------------------
# 10. FOOTER
# --------------------------------------------------



# --------------------------------------------------
# DAY 19: BUSINESS ALERTS
# --------------------------------------------------

if selected_section == "Overview":

    st.divider()
    st.header("Business Alerts")

    alerts = []

    # 1. Revenue alert
    if len(filtered_sales) >= 2:
        recent_sales = filtered_sales.sort_values("Date")

        recent_window = recent_sales.tail(7)
        baseline_window = recent_sales.iloc[:-7].tail(28)

        if not baseline_window.empty:
            baseline_revenue = baseline_window["TotalRevenue"].mean()
            recent_revenue = recent_window["TotalRevenue"].mean()

            if baseline_revenue > 0:
                revenue_change = (
                    (recent_revenue - baseline_revenue)
                    / baseline_revenue
                ) * 100

                if revenue_change <= -20:
                    alerts.append(
                        f"Revenue warning: recent average daily revenue "
                        f"is down {abs(revenue_change):.1f}% compared "
                        f"with the earlier baseline."
                    )

    # 2. Churn-risk alert
    if (
        not churn.empty
        and "ChurnRiskProbability" in churn.columns
    ):
        valid_probabilities = churn[
            "ChurnRiskProbability"
        ].dropna()

        high_risk_count = (
            valid_probabilities >= 0.70
        ).sum()

        if high_risk_count > 0:
            alerts.append(
                f"Churn review: {high_risk_count:,} records have "
                f"predicted churn-risk probabilities of 70% or higher."
            )

    # 3. Inventory reorder alert
    if (
        not inventory.empty
        and "InventoryStatus" in inventory.columns
    ):
        reorder_count = (
            inventory["InventoryStatus"]
            .astype(str)
            .str.contains("reorder", case=False, na=False)
            .sum()
        )

        if reorder_count > 0:
            alerts.append(
                f"Inventory review: {reorder_count:,} products "
                f"are marked for reorder in the simulated inventory data."
            )

    # Display alert summary
    if alerts:
        st.warning(
            f"{len(alerts)} business alert(s) require attention."
        )

        for alert in alerts:
            st.markdown(f"- {alert}")
    else:
        st.success(
            "No business alerts were triggered by the current rules."
        )

    st.caption(
        "Alerts are calculated from saved project outputs and the "
        "selected sales date range. They are not real-time notifications. "
        "Churn scores are proxy predictions; inventory recommendations "
        "use simulated stock values."
    )


st.divider()

st.caption(
    "RetailPulse | Built with Python, Pandas, Streamlit and Plotly"
)
