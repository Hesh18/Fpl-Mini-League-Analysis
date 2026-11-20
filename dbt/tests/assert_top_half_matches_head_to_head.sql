-- Fails if a manager's top-half weeks disagree with an independent count:
-- the weeks they outscored more than half of the other managers.
WITH teams AS (
    SELECT manager_id
    FROM {{ ref('stg_league_standings') }}
    WHERE snapshot_date = (SELECT max(snapshot_date) FROM {{ ref('stg_league_standings') }})
),

scores AS (
    SELECT m.manager_id, m.gameweek, m.points - m.transfer_cost AS net_points
    FROM {{ ref('stg_manager_gameweeks') }} AS m
    JOIN teams AS t ON t.manager_id = m.manager_id
    JOIN {{ ref('stg_gameweeks') }} AS g ON g.gameweek = m.gameweek
    WHERE g.is_final
),

head_to_head AS (
    SELECT
        a.manager_id,
        a.gameweek,
        count(*) FILTER (WHERE b.net_points < a.net_points) AS beaten,
        count(*) AS others
    FROM scores AS a
    JOIN scores AS b ON b.gameweek = a.gameweek AND b.manager_id <> a.manager_id
    GROUP BY a.manager_id, a.gameweek
),

expected AS (
    SELECT manager_id, count(*) FILTER (WHERE beaten * 2 > others) AS top_half_weeks
    FROM head_to_head
    GROUP BY manager_id
)

SELECT e.manager_id, e.top_half_weeks AS expected, m.top_half_weeks AS in_mart
FROM expected AS e
FULL OUTER JOIN {{ ref('mart_top_half_weeks') }} AS m ON m.manager_id = e.manager_id
WHERE e.top_half_weeks IS DISTINCT FROM m.top_half_weeks