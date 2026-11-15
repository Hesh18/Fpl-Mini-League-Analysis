-- Fails if FPL says a gameweek is final but we have no player points for it, or no most-captained player.
WITH loaded AS (
    SELECT DISTINCT gameweek
    FROM {{ ref('stg_gameweek_player_points') }}
)

SELECT g.gameweek, g.most_captained_player_id, l.gameweek AS loaded_gameweek
FROM {{ ref('stg_gameweeks') }} AS g
LEFT JOIN loaded AS l ON l.gameweek = g.gameweek
WHERE g.is_final
    AND (l.gameweek IS NULL OR g.most_captained_player_id IS NULL)