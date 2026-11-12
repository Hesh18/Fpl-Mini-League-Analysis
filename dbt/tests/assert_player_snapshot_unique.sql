-- Fails if a player appears more than once on the same day.
SELECT snapshot_date, player_id, count(*) AS copies
FROM {{ ref('stg_player_snapshots') }}
GROUP BY snapshot_date, player_id
HAVING count(*) > 1