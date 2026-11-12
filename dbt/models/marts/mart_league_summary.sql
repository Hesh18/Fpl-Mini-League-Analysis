-- One row per manager in the current league table, with season-long decision stats.
WITH latest_standings AS (
    SELECT *
    FROM {{ ref('stg_league_standings') }}
    WHERE snapshot_date = (SELECT max(snapshot_date) FROM {{ ref('stg_league_standings') }})
),

season_totals AS (
    SELECT
        manager_id,
        count(*) AS gameweeks_played,
        min(gameweek) AS first_gameweek,
        sum(points_on_bench) AS bench_points,
        sum(transfer_cost) AS hit_points,
        sum(transfers) AS transfers_made
    FROM {{ ref('stg_manager_gameweeks') }}
    GROUP BY manager_id
)

SELECT
    s.league_rank,
    s.manager_id,
    s.team_name,
    s.total_points,
    max(s.total_points) OVER () - s.total_points AS points_behind_leader,
    t.gameweeks_played,
    t.first_gameweek,
    t.bench_points,
    round(t.bench_points / t.gameweeks_played, 1) AS bench_points_per_gameweek,
    t.hit_points,
    t.transfers_made
FROM latest_standings AS s
JOIN season_totals AS t ON t.manager_id = s.manager_id