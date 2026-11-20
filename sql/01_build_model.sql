-- Olist sales and delivery analysis | PostgreSQL 14+
-- Aggregate order-level child tables before joining to prevent revenue fan-out.
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE TABLE IF NOT EXISTS staging.orders (order_id text PRIMARY KEY, customer_id text, order_status text, order_purchase_timestamp timestamp, order_approved_at timestamp, order_delivered_carrier_date timestamp, order_delivered_customer_date timestamp, order_estimated_delivery_date timestamp);
CREATE TABLE IF NOT EXISTS staging.order_items (order_id text, order_item_id integer, product_id text, seller_id text, shipping_limit_date timestamp, price numeric(12,2), freight_value numeric(12,2), PRIMARY KEY(order_id,order_item_id));
CREATE TABLE IF NOT EXISTS staging.order_payments (order_id text, payment_sequential integer, payment_type text, payment_installments integer, payment_value numeric(12,2));
CREATE TABLE IF NOT EXISTS staging.order_reviews (review_id text, order_id text, review_score integer, review_comment_title text, review_comment_message text, review_creation_date timestamp, review_answer_timestamp timestamp);
CREATE TABLE IF NOT EXISTS staging.customers (customer_id text PRIMARY KEY, customer_unique_id text, customer_zip_code_prefix text, customer_city text, customer_state text);
CREATE TABLE IF NOT EXISTS staging.products (product_id text PRIMARY KEY, product_category_name text, product_name_lenght integer, product_description_lenght integer, product_photos_qty integer, product_weight_g integer, product_length_cm integer, product_height_cm integer, product_width_cm integer);
CREATE TABLE IF NOT EXISTS staging.sellers (seller_id text PRIMARY KEY, seller_zip_code_prefix text, seller_city text, seller_state text);
CREATE TABLE IF NOT EXISTS staging.category_translation (product_category_name text PRIMARY KEY, product_category_name_english text);

CREATE OR REPLACE VIEW analytics.fact_order AS
WITH payment_by_order AS (
 SELECT order_id, SUM(payment_value) AS payment_value, COUNT(*) AS payment_transaction_count FROM staging.order_payments GROUP BY order_id
), review_by_order AS (
 SELECT order_id, AVG(review_score::numeric) AS review_score, COUNT(*) AS review_count FROM staging.order_reviews GROUP BY order_id
)
SELECT o.order_id,o.customer_id,c.customer_state,c.customer_city,o.order_status,o.order_purchase_timestamp,
 date_trunc('month',o.order_purchase_timestamp)::date AS purchase_month,o.order_delivered_customer_date,o.order_estimated_delivery_date,
 CASE WHEN o.order_delivered_customer_date IS NOT NULL AND o.order_estimated_delivery_date IS NOT NULL
 THEN o.order_delivered_customer_date::date-o.order_estimated_delivery_date::date END AS delivery_delay_days,
 p.payment_value,p.payment_transaction_count,r.review_score,r.review_count
FROM staging.orders o LEFT JOIN staging.customers c ON c.customer_id=o.customer_id
LEFT JOIN payment_by_order p ON p.order_id=o.order_id LEFT JOIN review_by_order r ON r.order_id=o.order_id;

CREATE OR REPLACE VIEW analytics.fact_order_item AS
SELECT i.order_id,i.order_item_id,i.product_id,i.seller_id,
 COALESCE(REPLACE(t.product_category_name_english,'_',' '),REPLACE(p.product_category_name,'_',' '),'Unknown') AS product_category,
 s.seller_state,i.price AS item_price,i.freight_value
FROM staging.order_items i LEFT JOIN staging.products p ON p.product_id=i.product_id
LEFT JOIN staging.category_translation t ON t.product_category_name=p.product_category_name
LEFT JOIN staging.sellers s ON s.seller_id=i.seller_id;

-- Export analytics.fact_order and analytics.fact_order_item as CSV for Power BI.
-- Category revenue ranking: merchandise only, excluding freight.
WITH category_sales AS (
 SELECT product_category,SUM(item_price) AS revenue,COUNT(DISTINCT order_id) AS orders FROM analytics.fact_order_item GROUP BY product_category
)
SELECT product_category,revenue,orders,RANK() OVER(ORDER BY revenue DESC) AS revenue_rank,
 ROUND(100.0*revenue/NULLIF(SUM(revenue) OVER(),0),2) AS revenue_share_pct FROM category_sales ORDER BY revenue_rank;

-- Revenue by customer state.
WITH state_sales AS (
 SELECT f.customer_state,SUM(i.item_price) AS revenue,COUNT(DISTINCT f.order_id) AS orders
 FROM analytics.fact_order f JOIN analytics.fact_order_item i USING(order_id) GROUP BY f.customer_state
)
SELECT customer_state,revenue,orders,RANK() OVER(ORDER BY revenue DESC) AS revenue_rank FROM state_sales ORDER BY revenue_rank;

-- Monthly AOV and month-over-month change; each order is counted once.
WITH monthly AS (
 SELECT date_trunc('month',o.order_purchase_timestamp)::date AS purchase_month,SUM(i.price) AS revenue,COUNT(DISTINCT o.order_id) AS orders
 FROM staging.orders o JOIN staging.order_items i USING(order_id) WHERE o.order_purchase_timestamp IS NOT NULL GROUP BY 1
), aov AS (SELECT purchase_month,revenue,orders,revenue/NULLIF(orders,0) AS average_order_value FROM monthly)
SELECT purchase_month,revenue,orders,ROUND(average_order_value,2) AS average_order_value,
 ROUND(average_order_value-LAG(average_order_value) OVER(ORDER BY purchase_month),2) AS aov_change_from_prior_month FROM aov ORDER BY purchase_month;

-- Delivery-delay bucket versus average review. Delay = delivery date minus estimate.
WITH bucketed AS (
 SELECT order_id,review_score,delivery_delay_days,
 CASE WHEN delivery_delay_days IS NULL THEN 'Not delivered / missing dates' WHEN delivery_delay_days<=0 THEN 'On time'
 WHEN delivery_delay_days<=3 THEN '1-3 days late' WHEN delivery_delay_days<=7 THEN '4-7 days late' ELSE '8+ days late' END AS delay_bucket
 FROM analytics.fact_order
)
SELECT delay_bucket,COUNT(*) AS orders,ROUND(AVG(review_score),2) AS average_review_score,
 ROUND(100.0*COUNT(*) FILTER(WHERE review_score<=2)/NULLIF(COUNT(review_score),0),2) AS low_review_pct
FROM bucketed GROUP BY delay_bucket
ORDER BY CASE delay_bucket WHEN 'On time' THEN 1 WHEN '1-3 days late' THEN 2 WHEN '4-7 days late' THEN 3 WHEN '8+ days late' THEN 4 ELSE 5 END;
