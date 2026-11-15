-- Fails if a squad isn't 15 players with 11 picked to start, one captain and at most one armband.
SELECT
    manager_id,
    gameweek,
    count(*) AS squad_size,
    count(*) FILTER (WHERE picked_to_start) AS starters,
    count(*) FILTER (WHERE is_captain) AS captains,
    count(*) FILTER (WHERE multiplier >= 2) AS armbands
FROM {{ ref('stg_manager_picks') }}
GROUP BY manager_id, gameweek
HAVING count(*) <> 15
    OR count(*) FILTER (WHERE picked_to_start) <> 11
    OR count(*) FILTER (WHERE is_captain) <> 1
    OR count(*) FILTER (WHERE multiplier >= 2) > 1