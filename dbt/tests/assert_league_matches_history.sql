-- Fails if the latest league table disagrees with a manager's own history.
-- While a gameweek is still being played, FPL updates the league table and each manager's
-- history at different moments, so only the points from finished gameweeks are compared.
-- The league's gameweek points don't include transfer hits, but its total does, so the hit is added back.
WITH league AS (
    SELECT manager_id, total_points, gameweek_points
    FROM {{ ref('stg_league_standings') }}
    WHERE snapshot_date = (SELECT max(snapshot_date) FROM {{ ref('stg_league_standings') }})
),

history AS (
    SELECT
        manager_id,
        total_points,
        transfer_cost,
        coalesce(lag(total_points) OVER (PARTITION BY manager_id ORDER BY gameweek), 0) AS total_before_this_gameweek
    FROM {{ ref('stg_manager_gameweeks') }}
    QUALIFY row_number() OVER (PARTITION BY manager_id ORDER BY gameweek DESC) = 1
),

latest_status AS (
    SELECT coalesce(g.is_final, false) AS is_final
    FROM (SELECT max(gameweek) AS gameweek FROM {{ ref('stg_manager_gameweeks') }}) AS latest
    LEFT JOIN {{ ref('stg_gameweeks') }} AS g ON g.gameweek = latest.gameweek
)

SELECT l.manager_id, l.total_points AS league_total, h.total_points AS history_total
FROM league AS l
LEFT JOIN history AS h ON h.manager_id = l.manager_id
CROSS JOIN latest_status AS s
WHERE h.manager_id IS NULL
    OR (s.is_final AND l.total_points <> h.total_points)
    OR (NOT s.is_final AND l.total_points - l.gameweek_points + h.transfer_cost <> h.total_before_this_gameweek)
