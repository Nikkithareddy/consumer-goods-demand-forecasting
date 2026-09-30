-- Consumer Goods Demand Forecasting & Safety Stock Optimization
-- Run against data/daily_sales.csv loaded into a `sales` table (see src/load_to_sqlite.py)

-- 1. Seasonal average demand per category per month
SELECT
    category,
    CAST(strftime('%m', date) AS INTEGER) AS month,
    ROUND(AVG(units_sold), 1) AS avg_units_sold
FROM sales
GROUP BY category, month
ORDER BY category, month;

-- 2. Promotional lift: average units sold on-promo vs off-promo, per category
SELECT
    category,
    ROUND(AVG(CASE WHEN on_promo = 1 THEN units_sold END), 1) AS avg_units_on_promo,
    ROUND(AVG(CASE WHEN on_promo = 0 THEN units_sold END), 1) AS avg_units_off_promo,
    ROUND(
        100.0 * (AVG(CASE WHEN on_promo = 1 THEN units_sold END)
                 - AVG(CASE WHEN on_promo = 0 THEN units_sold END))
        / AVG(CASE WHEN on_promo = 0 THEN units_sold END), 1
    ) AS promo_lift_pct
FROM sales
GROUP BY category
ORDER BY promo_lift_pct DESC;

-- 3. Rolling 7-day average demand per category (trend smoothing for forecasting)
SELECT
    category,
    date,
    units_sold,
    ROUND(AVG(units_sold) OVER (
        PARTITION BY category ORDER BY date
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ), 1) AS rolling_7d_avg
FROM sales
ORDER BY category, date;

-- 4. Demand volatility (coefficient of variation) per category
-- Higher CV => more safety stock needed for the same target service level
SELECT
    category,
    ROUND(AVG(units_sold), 1) AS mean_demand,
    ROUND(
        SQRT(AVG(units_sold * units_sold) - AVG(units_sold) * AVG(units_sold)), 1
    ) AS demand_stddev,
    ROUND(
        100.0 * SQRT(AVG(units_sold * units_sold) - AVG(units_sold) * AVG(units_sold))
        / AVG(units_sold), 1
    ) AS coefficient_of_variation_pct
FROM sales
GROUP BY category
ORDER BY coefficient_of_variation_pct DESC;

-- 5. Weekday vs weekend demand pattern per category
SELECT
    category,
    CASE WHEN CAST(strftime('%w', date) AS INTEGER) IN (0, 6) THEN 'Weekend' ELSE 'Weekday' END AS day_type,
    ROUND(AVG(units_sold), 1) AS avg_units_sold
FROM sales
GROUP BY category, day_type
ORDER BY category, day_type;
