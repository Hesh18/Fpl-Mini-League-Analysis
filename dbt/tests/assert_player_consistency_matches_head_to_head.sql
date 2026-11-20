-- Fails if a player's good games disagree with an independent count:
-- full games where he outscored more than half of the other players in his position who also played a full game.
WITH positions AS (
    SELECT player_id, position
    FROM {{ ref('stg_player_snapshots') }}
    WHERE snapshot_date = (SELECT max(snapshot_date) FROM {{ ref('stg_player_snapshots') }})
),

full_games AS (
    SELECT pts.player_id, pts.gameweek, pts.points, p.position
    FROM {{ ref('stg_gameweek_player_points') }} AS pts
    JOIN positions AS p ON p.player_id = pts.player_id
    WHERE pts.minutes >= 60
),

head_to_head AS (
    SELECT
        a.player_id,
        a.gameweek,
        count(*) FILTER (WHERE b.points < a.points) AS beaten,
        count(*) AS others
    FROM full_games AS a
    JOIN full_games AS b
        ON b.gameweek = a.gameweek
        AND b.position = a.position
        AND b.player_id <> a.player_id
    GROUP BY a.player_id, a.gameweek
),

expected AS (
    SELECT player_id, count(*) FILTER (WHERE beaten * 2 > others) AS good_games
    FROM head_to_head
    GROUP BY player_id
)

SELECT e.player_id, e.good_games AS expected, m.good_games AS in_mart
FROM expected AS e
FULL OUTER JOIN {{ ref('mart_player_consistency') }} AS m ON m.player_id = e.player_id
WHERE e.good_games IS DISTINCT FROM m.good_games