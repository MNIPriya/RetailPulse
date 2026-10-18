# RetailPulse — AI-Powered Retail Analytics & Demand Forecasting

## Overview

RetailPulse is an end-to-end retail analytics platform developed to transform retail transaction data into meaningful business insights. It combines data analysis, machine learning, time-series forecasting, and an interactive Streamlit dashboard to help users explore sales performance, customer behavior, revenue trends, churn risk, and inventory recommendations.

The project demonstrates how data-driven techniques can support retail business decision-making.

## Business Objectives

- Analyze revenue and sales trends over time.
- Segment customers based on purchasing behavior.
- Forecast future revenue and compare forecasting models.
- Identify customers who may be at risk of becoming inactive.
- Generate inventory reorder recommendations using estimated demand.
- Detect changes in customer data using statistical drift tests.
- Automate daily sales data processing.
- Present results through an interactive dashboard with downloadable reports.

## Key Features

### 1. Sales Analytics
- Revenue and transaction analysis.
- Daily and monthly revenue trends.
- Interactive date filters and business alerts.

### 2. Customer Segmentation
- Recency, Frequency, and Monetary (RFM) analysis.
- K-Means clustering and DBSCAN exploration.
- Customer cluster summaries and visualizations.

### 3. Revenue Forecasting
- Prophet forecasting model.
- LSTM deep-learning model.
- Ensemble forecasting using a combination of model predictions.
- Model evaluation using MAE, RMSE, and WAPE.
- What-if analysis to explore alternative revenue scenarios.

### 4. Customer Churn Risk Analysis
- Customer feature engineering.
- Random Forest classification.
- Churn-risk probability exploration.
- Feature importance and SHAP-based explainability.

### 5. Inventory Recommendations
- Product-level demand analysis.
- Estimated safety stock and reorder points.
- Inventory status filtering and visual analysis.

### 6. Data Drift Detection
- Statistical comparison of reference and incoming customer data.
- Kolmogorov–Smirnov tests and multiple-testing correction.

### 7. Automated Data Pipeline
- Apache Airflow DAG for checking input data and processing daily sales summaries.

### 8. Interactive Dashboard
- Streamlit dashboard with multiple analysis sections.
- Interactive charts and filters.
- Business alerts.
- CSV and PDF report downloads.

## Technology Stack

- **Programming:** Python
- **Data Analysis:** Pandas, NumPy
- **Visualization:** Plotly, Matplotlib
- **Machine Learning:** Scikit-learn
- **Deep Learning:** PyTorch
- **Forecasting:** Prophet
- **Model Explainability:** SHAP
- **Dashboard:** Streamlit
- **Workflow Automation:** Apache Airflow
- **Database / Querying Skills:** SQL
- **Reporting:** ReportLab
- **Version Control:** Git and GitHub
- **Containerization:** Docker setup in progress

## Dataset

This project uses the UCI Online Retail dataset, which contains retail transaction records and fields such as invoice number, product code, product description, quantity, invoice date, unit price, customer ID, and country.

The dataset is used to derive sales metrics, customer features, product demand estimates, and forecasting inputs.

## Project Structure

```text
RetailPulse/
├── data/                 # Input dataset
├── notebook/             # Analysis and ML notebooks
├── outputs/              # Generated datasets and model results
├── scripts/              # Dashboard and pipeline scripts
├── dags/                 # Airflow DAG definitions
├── requirements.txt      # Python dependencies
├── README.md             # Project documentation
├── .gitignore            # Files excluded from Git
├── .dockerignore         # Files excluded from Docker build context
└── Dockerfile            # Docker image configuration
```

## Run the Streamlit Dashboard Locally

### 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd RetailPulse
```

Replace `YOUR_GITHUB_REPOSITORY_URL` with your actual GitHub repository URL.

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Launch the dashboard

```bash
python -m streamlit run scripts/streamlit_app.py
```

Open the local URL displayed in the terminal, usually `http://localhost:8501`.

Ensure the required CSV files are available in the expected `outputs/` directory before launching the dashboard.

## Important Assumptions and Limitations

- **Churn:** Customer churn is represented using purchase inactivity as a proxy label. It is not a confirmed business churn label.
- **Inventory:** The original dataset does not contain actual stock-on-hand or supplier lead-time records. Inventory levels and certain operational parameters are simulated or assumed for demonstration.
- **Data drift:** The incoming batch used in the drift experiment is simulated to demonstrate drift detection; it is not a live production data stream.
- **Forecasting:** Model performance depends on the historical data, feature choices, forecast horizon, and evaluation method.
- **Deployment:** The dashboard currently runs locally. Docker and further deployment infrastructure remain in progress.

## Future Improvements

- Deploy the dashboard to a public hosting platform.
- Complete Docker containerization and Kubernetes deployment.
- Add live data ingestion and automated model retraining.
- Integrate real inventory and supplier data.
- Improve forecasting and churn model evaluation.
- Add continuous integration and production monitoring.

## Project Goal

RetailPulse demonstrates an end-to-end analytics workflow—from data preparation and machine learning to interactive reporting—using a retail transaction dataset. It showcases practical skills in data analytics, predictive modeling, dashboard development, and workflow automation.