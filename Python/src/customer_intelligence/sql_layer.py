from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd


def build_sqlite_database(
    database_path: Path,
    raw_tables: dict[str, pd.DataFrame],
    processed_tables: dict[str, pd.DataFrame],
) -> None:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    if database_path.exists():
        database_path.unlink()
    with sqlite3.connect(database_path) as connection:
        for name, frame in {**raw_tables, **processed_tables}.items():
            export = frame.copy()
            for column in export.select_dtypes(include=["datetime64[ns]"]).columns:
                export[column] = export[column].dt.strftime("%Y-%m-%d")
            export.to_sql(name, connection, if_exists="replace", index=False)
        connection.executescript(
            """
            CREATE INDEX IF NOT EXISTS idx_orders_customer
                ON fact_orders(customer_id);
            CREATE INDEX IF NOT EXISTS idx_orders_date
                ON fact_orders(order_date);
            CREATE INDEX IF NOT EXISTS idx_order_lines_order
                ON fact_order_lines(order_id);
            CREATE INDEX IF NOT EXISTS idx_interactions_customer_month
                ON fact_interactions_monthly(customer_id, month);
            CREATE INDEX IF NOT EXISTS idx_customer_360_customer
                ON customer_360(customer_id);

            DROP VIEW IF EXISTS vw_executive_customer_intelligence;
            CREATE VIEW vw_executive_customer_intelligence AS
            SELECT
                rfm_segment,
                risk_band,
                clv_band,
                COUNT(*) AS customers,
                SUM(monetary_12m) AS revenue_12m,
                SUM(gross_margin_12m) AS gross_margin_12m,
                SUM(predicted_clv_12m) AS predicted_clv_12m,
                AVG(churn_probability) AS avg_churn_probability,
                SUM(expected_incremental_margin) AS expected_incremental_margin
            FROM customer_360
            GROUP BY rfm_segment, risk_band, clv_band;

            DROP VIEW IF EXISTS vw_campaign_portfolio;
            CREATE VIEW vw_campaign_portfolio AS
            SELECT
                recommended_action,
                campaign_priority,
                COUNT(*) AS targeted_customers,
                SUM(allocated_budget) AS allocated_budget,
                SUM(expected_incremental_margin) AS expected_incremental_margin,
                AVG(expected_roi) AS average_expected_roi
            FROM campaign_targets
            WHERE selected_for_campaign = 1
            GROUP BY recommended_action, campaign_priority;
            """
        )


def query_scalar(database_path: Path, query: str) -> float:
    with sqlite3.connect(database_path) as connection:
        row = connection.execute(query).fetchone()
    if row is None or row[0] is None:
        return 0.0
    return float(row[0])

