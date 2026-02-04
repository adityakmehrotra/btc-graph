-- Query 1: Global summary of all address
-- “Across the entire a2a table, how many transfers are there, how much value moved in total, and what’s the average transfer size?”
SELECT
  COUNT(*) AS num_edges,
  SUM(value_satoshi) AS total_sats,
  AVG(value_satoshi) AS avg_sats
FROM a2a;

-- Query 2: Summary stats for “whale” transfers (≥ 10 BTC)
-- “How many whale-sized transfers happened, how much value did they move total, and what was the biggest one?”
SELECT
  COUNT(*) AS whale_edges,
  SUM(value_satoshi) AS whale_sats,
  MAX(value_satoshi) AS max_whale_sats
FROM a2a
WHERE value_satoshi >= 1000000000;

-- Query 3: Distribution of transfers by value bucket (<0.001 BTC, 0.001–0.1, 0.1–10, ≥10)
-- “How is transfer activity/value distributed across small vs medium vs large transfers, and which size bucket carries the most total value?”
WITH agg AS (
    SELECT
      CASE
        WHEN value_satoshi < 100000 THEN 0
        WHEN value_satoshi < 10000000 THEN 1
        WHEN value_satoshi < 1000000000 THEN 2
        ELSE 3
      END AS bucket_id,
      COUNT(*) AS n,
      SUM(value_satoshi) AS sats
    FROM a2a
    GROUP BY bucket_id
  )
  SELECT
    CASE bucket_id
      WHEN 0 THEN '<0.001 BTC'
      WHEN 1 THEN '0.001-0.1 BTC'
      WHEN 2 THEN '0.1-10 BTC'
      ELSE '>=10 BTC'
    END AS bucket,
    n,
    sats
  FROM agg
  ORDER BY sats DESC;

-- Query 4: Top 50 destination IDs by total inflow and number of incoming edges
-- “Which destination nodes receive the most total value (and how many incoming transfers do they get)?”
SELECT
  dst_id,
  SUM(value_satoshi) AS inflow_sats,
  COUNT(*) AS in_edges
FROM a2a_id
GROUP BY dst_id
ORDER BY inflow_sats DESC
LIMIT 50;

-- Query 5: Top 50 source IDs by total outflow and number of outgoing edges
-- “Which source nodes send the most total value (and how many outgoing transfers do they create)?”
SELECT
  src_id,
  SUM(value_satoshi) AS outflow_sats,
  COUNT(*) AS out_edges
FROM a2a_id
GROUP BY src_id
ORDER BY outflow_sats DESC
LIMIT 50;

-- Query 6: Identifies “fan-out” transactions with many outputs (≥ 50)
-- “Which transactions create unusually many outputs, and how much total value do those high-fanout transactions distribute?”
SELECT
  txid_id,
  COUNT(*) AS num_outputs,
  SUM(value_satoshi) AS total_sats
FROM a2a_tid
GROUP BY txid_id
HAVING COUNT(*) >= 50
ORDER BY num_outputs DESC
LIMIT 50;

-- Query 7: Two-hop “whale flow forwarding” ranking: pick top whale-receiving intermediates (mid nodes by inbound ≥10 BTC), then see where they forward ≥0.1 BTC transfers, returning top second-hop destinations by forwarded sats
-- “From top whale-receiving intermediaries, which second-hop nodes receive the most value forwarded onward (via transfers ≥0.1 BTC), and through how many such paths?”
WITH whale_mids AS (
  SELECT
    dst_id AS mid_id,
    SUM(value_satoshi) AS inbound_sats
  FROM a2a_id
  WHERE value_satoshi >= 1000000000
  GROUP BY dst_id
  ORDER BY inbound_sats DESC
  LIMIT 5000
),
hop2 AS (
  SELECT
    src_id AS mid_id,
    dst_id AS second_hop_id,
    value_satoshi
  FROM a2a_id
  WHERE value_satoshi >= 10000000
)
SELECT
  second_hop_id,
  SUM(value_satoshi) AS forwarded_sats,
  COUNT(*) AS paths
FROM whale_mids
JOIN hop2 USING (mid_id)
GROUP BY second_hop_id
ORDER BY forwarded_sats DESC
LIMIT 50;
