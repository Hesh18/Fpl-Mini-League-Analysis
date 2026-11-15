-- One row per player per final gameweek: minutes played and FPL points scored.
WITH files AS (
    SELECT
        CAST(regexp_extract(filename, '(\d+)\.json\.gz$', 1) AS BIGINT) AS gameweek,
        elements
    FROM {{ source('fpl_raw', 'gameweek_live') }}
),

players AS (
    SELECT gameweek, unnest(elements) AS e
    FROM files
)

SELECT
    gameweek,
    e.id AS player_id,
    CAST(e.stats.minutes AS BIGINT) AS minutes,
    CAST(e.stats.total_points AS BIGINT) AS points
FROM players