from pathlib import Path
import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parents[1]
INPUT_FILE = PROJECT_DIR / "outputs" / "day2_sales_data.csv"
OUTPUT_DIR = PROJECT_DIR / "outputs"


def process_daily_sales():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}"
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(INPUT_FILE, parse_dates=["InvoiceDate"])

    required_columns = [
        "InvoiceDate",
        "Quantity",
        "UnitPrice",
        "InvoiceNo",
    ]

    missing = set(required_columns) - set(df.columns)

    if missing:
        raise ValueError(
            f"Missing required columns: {sorted(missing)}"
        )

    df = df.dropna(subset=["InvoiceDate", "InvoiceNo"]).copy()

    df["Revenue"] = df["Quantity"] * df["UnitPrice"]
    df["Date"] = df["InvoiceDate"].dt.normalize()

    daily_summary = (
        df.groupby("Date")
        .agg(
            TotalRevenue=("Revenue", "sum"),
            TotalUnits=("Quantity", "sum"),
            TotalInvoices=("InvoiceNo", "nunique"),
        )
        .reset_index()
    )

    output_file = OUTPUT_DIR / "day13_daily_sales_summary.csv"
    daily_summary.to_csv(output_file, index=False)

    print(f"Processed {len(df):,} transaction rows.")
    print(f"Saved daily summary to: {output_file}")

    return str(output_file)


if __name__ == "__main__":
    process_daily_sales()