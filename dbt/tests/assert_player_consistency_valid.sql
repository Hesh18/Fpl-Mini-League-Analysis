-- Fails if the counts contradict each other or the 40% rule:
-- more good games than full games, more full games than finished gameweeks,
-- or a player ranked (or left out) against the rule.
WITH finished AS (
    SELECT count(DISTINCT gameweek) AS gameweeks
    FROM {{ ref('stg_gameweek_player_points') }}
)

SELECT m.*
FROM {{ ref('mart_player_consistency') }} AS m
CROSS JOIN finished AS f
WHERE m.good_games > m.full_games
    OR m.full_games > f.gameweeks
    OR m.is_ranked IS DISTINCT FROM (m.full_games >= 0.4 * f.gameweeks)