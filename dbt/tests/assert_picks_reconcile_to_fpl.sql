-- Fails if a manager's picks don't add up to the gameweek points and bench points FPL reports.
WITH computed AS (
    SELECT
        p.manager_id,
        p.gameweek,
        sum(pts.points * p.multiplier) AS computed_points,
        sum(CASE WHEN p.multiplier = 0 THEN pts.points ELSE 0 END) AS computed_bench_points
    FROM {{ ref('stg_manager_picks') }} AS p
    LEFT JOIN {{ ref('stg_gameweek_player_points') }} AS pts
        ON pts.gameweek = p.gameweek
        AND pts.player_id = p.player_id
    GROUP BY p.manager_id, p.gameweek
)

SELECT c.manager_id, c.gameweek, c.computed_points, g.points, c.computed_bench_points, g.points_on_bench
FROM computed AS c
LEFT JOIN {{ ref('stg_manager_gameweeks') }} AS g
    ON g.manager_id = c.manager_id
    AND g.gameweek = c.gameweek
WHERE c.computed_points IS DISTINCT FROM g.points
    OR c.computed_bench_points IS DISTINCT FROM g.points_on_bench