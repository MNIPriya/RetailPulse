
from datetime import datetime

from airflow.sdk import DAG
from airflow.providers.standard.operators.bash import BashOperator

with DAG(
    dag_id="retailpulse_daily_pipeline",
    description="Process RetailPulse sales data into a daily summary",
    start_date=datetime(2026, 1, 1),
    schedule="@daily",
    catchup=False,
    tags=["retailpulse", "analytics"],
) as dag:

    check_input = BashOperator(
        task_id="check_input_file",
        bash_command=(
            "test -f "
            "/opt/airflow/retailpulse/outputs/day2_sales_data.csv"
        ),
    )

    process_sales = BashOperator(
        task_id="process_daily_sales",
        bash_command=(
            "python "
            "/opt/airflow/retailpulse/scripts/daily_sales_pipeline.py"
        ),
    )

    check_input >> process_sales
