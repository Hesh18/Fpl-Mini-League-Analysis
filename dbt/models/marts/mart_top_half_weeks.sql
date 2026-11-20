-- One row per manager: how often they finished in the top half of the league, and their longest and current runs of top-half weeks.
WITH teams AS (
    SELECT manager_id, team_name
    FROM {{ ref('stg_league_standings') }}
    WHERE snapshot_date = (SELECT max(snapshot_date) FROM {{ ref('stg_league_standings') }})
),

scores AS (
    SELECT
        m.manager_id,
        m.gameweek,
        m.points - m.transfer_cost AS net_points
    FROM {{ ref('stg_manager_gameweeks') }} AS m
    JOIN teams AS t ON t.manager_id = m.manager_id
    JOIN {{ ref('stg_gameweeks') }} AS g ON g.gameweek = m.gameweek
    WHERE g.is_final
),

weeks AS (
    SELECT
        manager_id,
        gameweek,
        net_points > median(net_points) OVER (PARTITION BY gameweek) AS top_half
    FROM scores
),

runs AS (
    SELECT
        manager_id,
        gameweek,
        top_half,
        count(*) FILTER (WHERE NOT top_half) OVER (PARTITION BY manager_id ORDER BY gameweek) AS run_id
    FROM weeks
),

run_lengths AS (
    SELECT
        manager_id,
        run_id,
        count(*) FILTER (WHERE top_half) AS run_length
    FROM runs
    GROUP BY manager_id, run_id
),

run_summary AS (
    SELECT
        manager_id,
        max(run_length) AS longest_run,
        arg_max(run_length, run_id) AS current_run
    FROM run_lengths
    GROUP BY manager_id
),

week_summary AS (
    SELECT
        manager_id,
        count(*) AS gameweeks_played,
        count(*) FILTER (WHERE top_half) AS top_half_weeks
    FROM weeks
    GROUP BY manager_id
)

SELECT
    t.manager_id,
    t.team_name,
    w.gameweeks_played,
    w.top_half_weeks,
    round(w.top_half_weeks / w.gameweeks_played, 3) AS top_half_share,
    r.longest_run,
    r.current_run
FROM teams AS t
JOIN week_summary AS w ON w.manager_id = t.manager_id
JOIN run_summary AS r ON r.manager_id = t.manager_id