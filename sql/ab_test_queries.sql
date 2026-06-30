-- ==============================================================================
-- PRODUCT ANALYTICS & A/B TESTING: SQL ANALYSIS SCRIPTS
-- Recommended Dialect: BigQuery SQL / Standard ANSI SQL
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 1. CONVERSION FUNNEL ANALYSIS (CONTROL VS. TREATMENT)
-- Calculates the unique user counts, overall conversion rates, and step-relative
-- conversion rates across the 5 onboarding steps:
-- sign_up -> email_verified -> tutorial_start -> tutorial_complete -> purchase
-- ------------------------------------------------------------------------------

WITH user_cohort AS (
  -- Get all users participating in the A/B test phase (March 1st onwards)
  SELECT 
    user_id,
    ab_variant
  FROM `data-project.analytics.raw_user_demographics`
  WHERE ab_variant IN ('control', 'treatment')
),

funnel_counts AS (
  -- Count unique users who reached each event stage
  SELECT
    u.ab_variant,
    COUNT(DISTINCT u.user_id) AS signup_count,
    COUNT(DISTINCT CASE WHEN e.event_name = 'email_verified' THEN u.user_id END) AS email_verified_count,
    COUNT(DISTINCT CASE WHEN e.event_name = 'tutorial_start' THEN u.user_id END) AS tutorial_start_count,
    COUNT(DISTINCT CASE WHEN e.event_name = 'tutorial_complete' THEN u.user_id END) AS tutorial_complete_count,
    COUNT(DISTINCT CASE WHEN e.event_name = 'purchase' THEN u.user_id END) AS purchase_count
  FROM user_cohort u
  LEFT JOIN `data-project.analytics.raw_user_events` e 
    ON u.user_id = e.user_id
  GROUP BY u.ab_variant
)

-- Pivot and calculate funnel ratios
SELECT 
  ab_variant,
  '1_sign_up' AS funnel_stage,
  signup_count AS active_users,
  1.0 AS pct_overall,
  1.0 AS pct_relative
FROM funnel_counts

UNION ALL

SELECT 
  ab_variant,
  '2_email_verified' AS funnel_stage,
  email_verified_count AS active_users,
  ROUND(SAFE_DIVIDE(email_verified_count, signup_count), 4) AS pct_overall,
  ROUND(SAFE_DIVIDE(email_verified_count, signup_count), 4) AS pct_relative
FROM funnel_counts

UNION ALL

SELECT 
  ab_variant,
  '3_tutorial_start' AS funnel_stage,
  tutorial_start_count AS active_users,
  ROUND(SAFE_DIVIDE(tutorial_start_count, signup_count), 4) AS pct_overall,
  ROUND(SAFE_DIVIDE(tutorial_start_count, email_verified_count), 4) AS pct_relative
FROM funnel_counts

UNION ALL

SELECT 
  ab_variant,
  '4_tutorial_complete' AS funnel_stage,
  tutorial_complete_count AS active_users,
  ROUND(SAFE_DIVIDE(tutorial_complete_count, signup_count), 4) AS pct_overall,
  ROUND(SAFE_DIVIDE(tutorial_complete_count, tutorial_start_count), 4) AS pct_relative
FROM funnel_counts

UNION ALL

SELECT 
  ab_variant,
  '5_purchase' AS funnel_stage,
  purchase_count AS active_users,
  ROUND(SAFE_DIVIDE(purchase_count, signup_count), 4) AS pct_overall,
  ROUND(SAFE_DIVIDE(purchase_count, tutorial_complete_count), 4) AS pct_relative
FROM funnel_counts
ORDER BY ab_variant, funnel_stage;


-- ------------------------------------------------------------------------------
-- 2. BASELINE COHORT RETENTION QUERY
-- Calculates weekly signup cohorts (pre-test phase) and measures the percentage
-- of unique users who return daily (Day 1 through Day 7) since their signup date.
-- ------------------------------------------------------------------------------

WITH pre_test_users AS (
  -- Filter to baseline users who signed up before the A/B test (Jan 1 to Feb 28)
  SELECT 
    user_id,
    CAST(signup_date AS DATE) AS signup_date,
    -- Group by week starting Monday
    DATE_TRUNC(CAST(signup_date AS DATE), WEEK(MONDAY)) AS cohort_week
  FROM `data-project.analytics.raw_user_demographics`
  WHERE ab_variant = 'not_applicable'
),

user_active_days AS (
  -- Find unique days user was active since their signup date
  SELECT 
    u.user_id,
    u.cohort_week,
    DATE_DIFF(CAST(e.timestamp AS DATE), u.signup_date, DAY) AS days_since_signup
  FROM pre_test_users u
  JOIN `data-project.analytics.raw_user_events` e 
    ON u.user_id = e.user_id
  -- We care about the first 7 days of activity
  WHERE DATE_DIFF(CAST(e.timestamp AS DATE), u.signup_date, DAY) BETWEEN 0 AND 7
),

cohort_sizes AS (
  -- Calculate size of each cohort (Day 0 unique users)
  SELECT 
    cohort_week,
    COUNT(DISTINCT user_id) AS cohort_size
  FROM pre_test_users
  GROUP BY cohort_week
)

-- Aggregate and calculate retention percentages per day since signup
SELECT 
  a.cohort_week,
  s.cohort_size,
  ROUND(COUNT(DISTINCT CASE WHEN a.days_since_signup = 0 THEN a.user_id END) / s.cohort_size, 4) AS day_0_pct,
  ROUND(COUNT(DISTINCT CASE WHEN a.days_since_signup = 1 THEN a.user_id END) / s.cohort_size, 4) AS day_1_pct,
  ROUND(COUNT(DISTINCT CASE WHEN a.days_since_signup = 2 THEN a.user_id END) / s.cohort_size, 4) AS day_2_pct,
  ROUND(COUNT(DISTINCT CASE WHEN a.days_since_signup = 3 THEN a.user_id END) / s.cohort_size, 4) AS day_3_pct,
  ROUND(COUNT(DISTINCT CASE WHEN a.days_since_signup = 4 THEN a.user_id END) / s.cohort_size, 4) AS day_4_pct,
  ROUND(COUNT(DISTINCT CASE WHEN a.days_since_signup = 5 THEN a.user_id END) / s.cohort_size, 4) AS day_5_pct,
  ROUND(COUNT(DISTINCT CASE WHEN a.days_since_signup = 6 THEN a.user_id END) / s.cohort_size, 4) AS day_6_pct,
  ROUND(COUNT(DISTINCT CASE WHEN a.days_since_signup = 7 THEN a.user_id END) / s.cohort_size, 4) AS day_7_pct
FROM user_active_days a
JOIN cohort_sizes s 
  ON a.cohort_week = s.cohort_week
GROUP BY a.cohort_week, s.cohort_size
ORDER BY a.cohort_week;


-- ------------------------------------------------------------------------------
-- 3. A/B TEST METRICS & REVENUE COMPARISON
-- Aggregates core conversion rates, average order values (AOV), and total revenue
-- per variant during the A/B testing phase.
-- ------------------------------------------------------------------------------

WITH ab_users AS (
  SELECT 
    user_id,
    ab_variant
  FROM `data-project.analytics.raw_user_demographics`
  WHERE ab_variant IN ('control', 'treatment')
),

user_orders AS (
  -- Get all purchase values for A/B users (ignoring duplicate records)
  SELECT DISTINCT
    e.event_id,
    e.user_id,
    e.event_value AS order_amount
  FROM `data-project.analytics.raw_user_events` e
  JOIN ab_users u 
    ON e.user_id = u.user_id
  WHERE e.event_name = 'purchase'
),

user_purchase_summary AS (
  -- Aggregate total purchase value and order counts per user
  SELECT 
    u.user_id,
    u.ab_variant,
    COUNT(o.event_id) AS total_orders,
    SUM(o.order_amount) AS total_spent
  FROM ab_users u
  LEFT JOIN user_orders o 
    ON u.user_id = o.user_id
  GROUP BY u.user_id, u.ab_variant
)

SELECT 
  ab_variant,
  COUNT(user_id) AS sample_size,
  -- Number of unique users who bought at least once
  COUNT(CASE WHEN total_orders > 0 THEN user_id END) AS converted_users,
  -- Purchase Conversion Rate
  ROUND(COUNT(CASE WHEN total_orders > 0 THEN user_id END) / COUNT(user_id), 4) AS conversion_rate,
  -- Total orders completed
  SUM(total_orders) AS total_completed_orders,
  -- Total Revenue
  ROUND(SUM(total_spent), 2) AS total_revenue,
  -- Average Order Value (AOV)
  ROUND(SUM(total_spent) / NULLIF(SUM(total_orders), 0), 2) AS average_order_value,
  -- Average Revenue Per User (ARPU)
  ROUND(SUM(total_spent) / COUNT(user_id), 2) AS average_revenue_per_user
FROM user_purchase_summary
GROUP BY ab_variant;
