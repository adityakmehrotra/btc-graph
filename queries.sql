-- RISK_THRESHOLD = 0.70;

-- Query 1: Top risky destinations (risky sinks)
-- “Which risky addresses receive the most value?”
WITH risky AS (
  SELECT address, risk_score
  FROM risk_labels
  WHERE risk_category = 'HIGH'
     OR risk_score >= 0.70
)
SELECT
  a.dst_address            AS address,
  SUM(a.value_satoshi)     AS total_inflow,
  COUNT(*)                 AS edges_in
FROM a2a AS a
JOIN risky AS r
  ON r.address = a.dst_address
GROUP BY 1
ORDER BY total_inflow DESC
LIMIT 20;

-- Query 2: Recipients most exposed to risky sources (direct 1-hop)
-- “Which recipients received the most value that originated from risky senders?”
WITH risky_src AS (
  SELECT address
  FROM risk_labels
  WHERE risk_category = 'HIGH'
     OR risk_score >= 0.70
)
SELECT
  a.dst_address                 AS address,
  SUM(a.value_satoshi)          AS total_in_from_risky,
  COUNT(*)                      AS edges_in_from_risky
FROM a2a AS a
JOIN risky_src AS r
  ON r.address = a.src_address
GROUP BY 1
ORDER BY total_in_from_risky DESC
LIMIT 200;
