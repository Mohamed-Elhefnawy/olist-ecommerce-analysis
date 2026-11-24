-- =============================================================
-- Olist E-Commerce: Business Questions in SQL
-- Database: SQLite built from the cleaned tables (data/clean/)
-- Every question starts from a business problem, not a chart.
-- =============================================================

-- Q1. How is revenue trending month over month?
-- Business use: growth tracking, seasonality, campaign timing.
SELECT
    purchase_month,
    ROUND(SUM(total_price), 2)        AS revenue_brl,
    COUNT(*)                          AS orders,
    ROUND(SUM(total_price) / COUNT(*), 2) AS avg_order_value_brl
FROM orders_master
WHERE purchase_month BETWEEN '2017-01' AND '2018-08'   -- complete months
GROUP BY purchase_month
ORDER BY purchase_month;

-- Q2. Which product categories drive the business?
-- Business use: assortment and marketing focus.
SELECT
    category_en,
    ROUND(SUM(price), 2)                          AS revenue_brl,
    ROUND(100.0 * SUM(price) / (SELECT SUM(price) FROM order_items_full), 1)
                                                  AS revenue_share_pct
FROM order_items_full
GROUP BY category_en
ORDER BY revenue_brl DESC
LIMIT 10;

-- Q3. Do late deliveries hurt customer satisfaction?
-- Business use: the cost of a broken delivery promise, in stars.
SELECT
    CASE WHEN is_late THEN 'late' ELSE 'on_time' END AS delivery_flag,
    COUNT(*)                            AS orders,
    ROUND(AVG(review_score), 2)         AS avg_review,
    ROUND(100.0 * SUM(CASE WHEN review_score = 1 THEN 1 ELSE 0 END) / COUNT(*), 1)
                                        AS pct_1_star
FROM orders_master
WHERE delivery_days IS NOT NULL AND review_score IS NOT NULL
GROUP BY delivery_flag;

-- Q4. How late is late, and how much revenue does it touch?
SELECT
    ROUND(AVG(delivery_days), 1)                          AS avg_delivery_days,
    ROUND(100.0 * AVG(is_late), 1)                        AS late_rate_pct,
    ROUND(SUM(CASE WHEN is_late THEN total_price ELSE 0 END), 2)
                                                          AS revenue_late_orders_brl
FROM orders_master
WHERE delivery_days IS NOT NULL;

-- Q5. What share of customers ever buy again?
-- Business use: retention, the cheapest revenue there is.
WITH orders_per_customer AS (
    SELECT customer_unique_id, COUNT(DISTINCT order_id) AS n_orders
    FROM orders_master
    GROUP BY customer_unique_id
)
SELECT
    COUNT(*)                                              AS customers,
    SUM(CASE WHEN n_orders > 1 THEN 1 ELSE 0 END)         AS repeat_customers,
    ROUND(100.0 * SUM(CASE WHEN n_orders > 1 THEN 1 ELSE 0 END) / COUNT(*), 1)
                                                          AS repeat_rate_pct
FROM orders_per_customer;

-- Q6. How do customers pay, and how much do installments matter?
-- Business use: payment friction and financing offers.
SELECT
    main_payment_type,
    COUNT(*)                                   AS orders,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM orders_master), 1)
                                               AS order_share_pct,
    ROUND(AVG(payment_installments), 1)        AS avg_installments
FROM orders_master
WHERE main_payment_type IS NOT NULL
GROUP BY main_payment_type
ORDER BY orders DESC;

-- Q7. How heavy is the freight burden?
-- Business use: margin protection and carrier negotiation.
SELECT
    ROUND(SUM(total_freight), 2)                              AS total_freight_brl,
    ROUND(100.0 * AVG(total_freight / NULLIF(total_price, 0)), 1)
                                                              AS avg_freight_share_pct
FROM orders_master
WHERE total_price > 0;

-- Q8. Where does revenue come from geographically?
SELECT
    customer_state,
    ROUND(SUM(total_price), 2) AS revenue_brl,
    ROUND(100.0 * SUM(total_price) / (SELECT SUM(total_price) FROM orders_master), 1)
                               AS revenue_share_pct
FROM orders_master
GROUP BY customer_state
ORDER BY revenue_brl DESC
LIMIT 5;
