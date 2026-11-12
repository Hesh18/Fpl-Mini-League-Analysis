-- Fails if the latest league table disagrees with a manager's own history.
WITH league AS (
    SELECT manager_id, total_points
    FROM {{ ref('stg_league_standings') }}
    WHERE snapshot_date = (SELECT max(snapshot_date) FROM {{ ref('stg_league_standings') }})
),

history AS (
    SELECT manager_id, total_points
    FROM {{ ref('stg_manager_gameweeks') }}
    QUALIFY row_number() OVER (PARTITION BY manager_id ORDER BY gameweek DESC) = 1
)

SELECT l.manager_id, l.total_points AS league_total, h.total_points AS history_total
FROM league AS l
LEFT JOIN history AS h ON h.manager_id = l.manager_id
WHERE h.total_points IS NULL OR l.total_points <> h.total_points