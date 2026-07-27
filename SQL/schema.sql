-- Customer Intelligence, CLV & Churn Prediction Platform
-- Portable relational schema for PostgreSQL-compatible warehouses.

CREATE TABLE dim_customers (
    customer_id VARCHAR(16) PRIMARY KEY,
    acquisition_date DATE NOT NULL,
    acquisition_channel VARCHAR(32) NOT NULL,
    preferred_channel VARCHAR(32) NOT NULL,
    region VARCHAR(40) NOT NULL,
    age_band VARCHAR(16) NOT NULL,
    loyalty_tier VARCHAR(16) NOT NULL,
    marketing_consent INTEGER NOT NULL,
    archetype VARCHAR(32) NOT NULL,
    attrition_date DATE,
    latent_value_index NUMERIC(10,4),
    engagement_index NUMERIC(10,4),
    price_sensitivity_index NUMERIC(10,4),
    service_friction_index NUMERIC(10,4)
);

CREATE TABLE dim_products (
    product_id VARCHAR(16) PRIMARY KEY,
    sku VARCHAR(32) UNIQUE NOT NULL,
    category VARCHAR(32) NOT NULL,
    product_name VARCHAR(120) NOT NULL,
    list_price NUMERIC(14,2) NOT NULL,
    standard_cost NUMERIC(14,2) NOT NULL,
    margin_pct NUMERIC(10,4) NOT NULL
);

CREATE TABLE fact_orders (
    order_id VARCHAR(20) PRIMARY KEY,
    customer_id VARCHAR(16) NOT NULL REFERENCES dim_customers(customer_id),
    order_date DATE NOT NULL,
    channel VARCHAR(32) NOT NULL,
    primary_category VARCHAR(32) NOT NULL,
    item_count INTEGER NOT NULL,
    gross_revenue NUMERIC(16,2) NOT NULL,
    discount_amount NUMERIC(16,2) NOT NULL,
    returned_amount NUMERIC(16,2) NOT NULL,
    net_revenue NUMERIC(16,2) NOT NULL,
    gross_margin NUMERIC(16,2) NOT NULL,
    returned_flag INTEGER NOT NULL
);

CREATE TABLE fact_order_lines (
    order_line_id VARCHAR(24) PRIMARY KEY,
    order_id VARCHAR(20) NOT NULL REFERENCES fact_orders(order_id),
    customer_id VARCHAR(16) NOT NULL REFERENCES dim_customers(customer_id),
    order_date DATE NOT NULL,
    product_id VARCHAR(16) NOT NULL REFERENCES dim_products(product_id),
    category VARCHAR(32) NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price NUMERIC(14,2) NOT NULL,
    discount_rate NUMERIC(10,4) NOT NULL,
    gross_revenue NUMERIC(16,2) NOT NULL,
    discount_amount NUMERIC(16,2) NOT NULL,
    returned_flag INTEGER NOT NULL,
    returned_amount NUMERIC(16,2) NOT NULL,
    net_revenue NUMERIC(16,2) NOT NULL,
    gross_margin NUMERIC(16,2) NOT NULL
);

CREATE TABLE fact_interactions_monthly (
    customer_id VARCHAR(16) NOT NULL REFERENCES dim_customers(customer_id),
    month DATE NOT NULL,
    sessions INTEGER NOT NULL,
    email_sent INTEGER NOT NULL,
    email_opens INTEGER NOT NULL,
    email_clicks INTEGER NOT NULL,
    support_tickets INTEGER NOT NULL,
    nps_score NUMERIC(4,1),
    PRIMARY KEY (customer_id, month)
);

CREATE INDEX idx_orders_customer_date ON fact_orders(customer_id, order_date);
CREATE INDEX idx_order_lines_product ON fact_order_lines(product_id);
CREATE INDEX idx_interactions_customer_month
    ON fact_interactions_monthly(customer_id, month);

