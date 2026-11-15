-- One row per manager per final gameweek: who wore the armband, and the best option they had.
WITH pick_points AS (
    SELECT
        p.manager_id,
        p.gameweek,
        p.player_id,
        p.squad_position,
        p.multiplier,
        p.is_vice_captain,
        p.chip,
        p.picked_to_start,
        pts.points
    FROM {{ ref('stg_manager_picks') }} AS p
    JOIN {{ ref('stg_gameweek_player_points') }} AS pts
        ON pts.gameweek = p.gameweek
        AND pts.player_id = p.player_id
),

best_option AS (
    SELECT manager_id, gameweek, chip, player_id, points
    FROM pick_points
    WHERE picked_to_start
    QUALIFY row_number() OVER (PARTITION BY manager_id, gameweek ORDER BY points DESC, multiplier DESC, squad_position) = 1
),

armband AS (
    SELECT manager_id, gameweek, player_id, points, is_vice_captain
    FROM pick_points
    WHERE multiplier >= 2
),

player_names AS (
    SELECT player_id, player_name
    FROM {{ ref('stg_player_snapshots') }}
    QUALIFY row_number() OVER (PARTITION BY player_id ORDER BY snapshot_date DESC) = 1
),

teams AS (
    SELECT manager_id, team_name
    FROM {{ ref('stg_league_standings') }}
    WHERE snapshot_date = (SELECT max(snapshot_date) FROM {{ ref('stg_league_standings') }})
)

SELECT
    b.gameweek,
    b.manager_id,
    t.team_name,
    b.chip,
    captain_name.player_name AS captain_name,
    coalesce(a.points, 0) AS captain_points,
    coalesce(a.is_vice_captain, false) AS vice_captain_stepped_in,
    best_name.player_name AS best_option_name,
    b.points AS best_option_points,
    CAST(
        (b.points - coalesce(a.points, 0)) * CASE WHEN b.chip = '3xc' THEN 2 ELSE 1 END
        AS BIGINT
    ) AS captain_points_lost
FROM best_option AS b
JOIN teams AS t ON t.manager_id = b.manager_id
LEFT JOIN armband AS a ON a.manager_id = b.manager_id AND a.gameweek = b.gameweek
LEFT JOIN player_names AS captain_name ON captain_name.player_id = a.player_id
LEFT JOIN player_names AS best_name ON best_name.player_id = b.player_id