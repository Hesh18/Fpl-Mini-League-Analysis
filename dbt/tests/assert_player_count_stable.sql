-- Fails if the player count changes by more than 5% from one snapshot day to the next.
WITH daily AS (
    SELECT snapshot_date, count(*) AS players
    FROM {{ ref('stg_player_snapshots') }}
    GROUP BY snapshot_date
),

compared AS (
    SELECT
        snapshot_date,
        players,
        lag(players) OVER (ORDER BY snapshot_date) AS previous_players
    FROM daily
)

SELECT snapshot_date, previous_players, players
FROM compared
WHERE previous_players IS NOT NULL
  AND abs(players - previous_players) > 0.05 * previous_players