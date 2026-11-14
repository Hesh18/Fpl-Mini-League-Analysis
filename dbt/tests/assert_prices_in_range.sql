-- Fails if a price is missing or outside a believable range in £m.
SELECT snapshot_date, player_id, player_name, price_m
FROM {{ ref('stg_player_snapshots') }}
WHERE price_m IS NULL OR price_m NOT BETWEEN 3.5 AND 20