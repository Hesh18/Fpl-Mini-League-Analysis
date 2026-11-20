-- One row per player who has played a full hour at least once: how often he beat the middle score of his own position.
WITH players AS (
    SELECT player_id, player_name, team_id, position, price_m
    FROM {{ ref('stg_player_snapshots') }}
    WHERE snapshot_date = (SELECT max(snapshot_date) FROM {{ ref('stg_player_snapshots') }})
),

full_games AS (
    SELECT pts.player_id, pts.gameweek, pts.points, p.position
    FROM {{ ref('stg_gameweek_player_points') }} AS pts
    JOIN players AS p ON p.player_id = pts.player_id
    WHERE pts.minutes >= 60
),

rated AS (
    SELECT
        player_id,
        points,
        points > median(points) OVER (PARTITION BY gameweek, position) AS good_game
    FROM full_games
),

finished AS (
    SELECT count(DISTINCT gameweek) AS gameweeks
    FROM {{ ref('stg_gameweek_player_points') }}
),

per_player AS (
    SELECT
        player_id,
        count(*) AS full_games,
        count(*) FILTER (WHERE good_game) AS good_games,
        max(points) AS best_game
    FROM rated
    GROUP BY player_id
)

SELECT
    p.player_id,
    p.player_name,
    t.team_name,
    p.position,
    p.price_m,
    s.full_games,
    s.good_games,
    round(s.good_games / s.full_games, 3) AS good_game_share,
    s.best_game,
    s.full_games >= 0.4 * f.gameweeks AS is_ranked
FROM per_player AS s
JOIN players AS p ON p.player_id = s.player_id
JOIN {{ ref('stg_teams') }} AS t ON t.team_id = p.team_id
CROSS JOIN finished AS f