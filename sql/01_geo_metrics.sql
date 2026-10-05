SELECT pair_id, geo_id, is_treatment, is_post,
       COUNT(*) AS days,
       AVG(conversions * 1.0) AS daily_conversions,
       SUM(revenue_usd) AS revenue_usd,
       SUM(spend_usd) AS channel_spend_usd,
       SUM(attributed_conversions) AS attributed_conversions
FROM geo_daily
GROUP BY pair_id, geo_id, is_treatment, is_post;
