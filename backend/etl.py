"""
ETL & Data Cleaning Pipeline
Loads sales transaction data, performs forensic data cleaning,
handles missing/corrupted values, converts date formats to ISO-8601,
computes net and gross revenue metrics, and loads into an indexed SQLite database.
"""

import os
import sqlite3
import pandas as pd
from typing import Dict, Any, List

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
RAW_CSV_PATH = os.path.join(DATA_DIR, "ai_bi_assistant_sales_data - GET.csv")
CLEANED_CSV_PATH = os.path.join(DATA_DIR, "cleaned_sales_data.csv")
DB_PATH = os.path.join(DATA_DIR, "sales_bi.db")

AUDIT_LOG: List[Dict[str, Any]] = []

def run_etl(raw_csv_path: str = RAW_CSV_PATH, db_path: str = DB_PATH) -> Dict[str, Any]:
    global AUDIT_LOG
    AUDIT_LOG = []
    
    if not os.path.exists(raw_csv_path):
        raise FileNotFoundError(f"Raw CSV file not found at: {raw_csv_path}")
        
    df = pd.read_csv(raw_csv_path)
    total_raw_rows = len(df)
    
    # 1. Clean Column Names (Standardize to lowercase snake_case)
    df.columns = [col.strip().lower() for col in df.columns]
    
    # 2. Forensic Cleaning of Numeric Fields
    # Detect corrupt/non-numeric values in unit_price
    df['unit_price'] = pd.to_numeric(df['unit_price'], errors='coerce')
    df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce').fillna(0).astype(int)
    df['discount_amount'] = pd.to_numeric(df['discount_amount'], errors='coerce').fillna(0).astype(float)
    
    # Identify rows with missing Unit_price (e.g., TXN0051)
    missing_price_mask = df['unit_price'].isna()
    for idx, row in df[missing_price_mask].iterrows():
        prod = row['product']
        # Find catalog price for this product from intact records
        valid_prices = df[(df['product'] == prod) & (~df['unit_price'].isna())]['unit_price']
        if not valid_prices.empty:
            imputed_price = float(valid_prices.mode()[0])
            df.at[idx, 'unit_price'] = imputed_price
            AUDIT_LOG.append({
                "transaction_id": row['transaction_id'],
                "issue": "Missing/Corrupted Unit_price",
                "action": f"Imputed unit_price={imputed_price} based on modal catalog price for product '{prod}'",
                "severity": "High",
                "resolved": True
            })
            
    # 3. Handle Edge Case: Returned orders (e.g., TXN0033)
    returned_mask = df['status'].str.strip().str.lower() == 'returned'
    for idx, row in df[returned_mask].iterrows():
        AUDIT_LOG.append({
            "transaction_id": row['transaction_id'],
            "issue": f"Status='Returned' detected",
            "action": "Preserved in database with status='Returned'; excluded from net completed revenue aggregations",
            "severity": "Medium",
            "resolved": True
        })

    # 4. Handle Edge Case: Zero Quantity (e.g., TXN0034)
    zero_qty_mask = df['quantity'] <= 0
    for idx, row in df[zero_qty_mask].iterrows():
        AUDIT_LOG.append({
            "transaction_id": row['transaction_id'],
            "issue": f"Zero quantity order detected (quantity={row['quantity']})",
            "action": "Preserved for transactional completeness; yields $0 gross and net revenue",
            "severity": "Low",
            "resolved": True
        })

    # 5. Date Standardisation: DD-MM-YYYY -> ISO-8601 YYYY-MM-DD
    # Parse DD-MM-YYYY
    parsed_dates = pd.to_datetime(df['order_date'], format='%d-%m-%Y', errors='coerce')
    df['order_date'] = parsed_dates.dt.strftime('%Y-%m-%d')
    df['order_month'] = parsed_dates.dt.strftime('%Y-%m')
    
    # 6. Computed Financial Fields
    df['gross_revenue'] = (df['quantity'] * df['unit_price']).round(2)
    df['net_revenue'] = (df['gross_revenue'] - df['discount_amount']).round(2)
    
    # Save Cleaned CSV
    os.makedirs(os.path.dirname(CLEANED_CSV_PATH), exist_ok=True)
    df.to_csv(CLEANED_CSV_PATH, index=False)
    
    # 7. Load into SQLite Database with Strict Typing & Indexes
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sales (
        transaction_id TEXT PRIMARY KEY,
        order_date TEXT NOT NULL,
        order_month TEXT NOT NULL,
        product TEXT NOT NULL,
        category TEXT NOT NULL,
        region TEXT NOT NULL,
        sales_channel TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        unit_price REAL NOT NULL,
        discount_amount REAL NOT NULL,
        gross_revenue REAL NOT NULL,
        net_revenue REAL NOT NULL,
        status TEXT NOT NULL
    );
    """)
    
    # Create Analytical Indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sales_date ON sales(order_date);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sales_month ON sales(order_month);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sales_product ON sales(product);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sales_region ON sales(region);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sales_status ON sales(status);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sales_category ON sales(category);")

    # Insert Rows
    insert_sql = """
    INSERT INTO sales (
        transaction_id, order_date, order_month, product, category,
        region, sales_channel, quantity, unit_price, discount_amount,
        gross_revenue, net_revenue, status
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """
    
    rows_to_insert = [
        (
            row['transaction_id'],
            row['order_date'],
            row['order_month'],
            row['product'],
            row['category'],
            row['region'],
            row['sales_channel'],
            int(row['quantity']),
            float(row['unit_price']),
            float(row['discount_amount']),
            float(row['gross_revenue']),
            float(row['net_revenue']),
            row['status']
        )
        for _, row in df.iterrows()
    ]
    cursor.executemany(insert_sql, rows_to_insert)
    conn.commit()
    conn.close()
    
    summary = {
        "status": "success",
        "total_raw_rows": total_raw_rows,
        "total_loaded_rows": len(rows_to_insert),
        "audit_issues_detected": len(AUDIT_LOG),
        "database_path": db_path,
        "cleaned_csv_path": CLEANED_CSV_PATH,
        "audit_log": AUDIT_LOG
    }
    return summary

def get_audit_log() -> List[Dict[str, Any]]:
    return AUDIT_LOG

if __name__ == "__main__":
    result = run_etl()
    print("ETL Execution Summary:")
    print(f"Loaded: {result['total_loaded_rows']} rows")
    print(f"Audit log items: {len(result['audit_log'])}")
    for item in result['audit_log']:
        print(f" - [{item['transaction_id']}] {item['issue']} -> {item['action']}")
