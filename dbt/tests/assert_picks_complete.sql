-- Fails if a manager played a final gameweek but we have no picks for it.
WITH final_gameweeks AS (
    SELECT DISTINCT gameweek
    FROM {{ ref('stg_gameweek_player_points') }}
),

picks AS (
    SELECT DISTINCT manager_id, gameweek
    FROM {{ ref('stg_manager_picks') }}
)

SELECT g.manager_id, g.gameweek
FROM {{ ref('stg_manager_gameweeks') }} AS g
JOIN final_gameweeks AS f ON f.gameweek = g.gameweek
LEFT JOIN picks AS p
    ON p.manager_id = g.manager_id
    AND p.gameweek = g.gameweek
WHERE p.manager_id IS NULL