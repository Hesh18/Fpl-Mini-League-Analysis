-- One row per gameweek, from the most recent snapshot: is it final, and who the whole game captained most.
WITH files AS (
    SELECT
        CAST(regexp_extract(filename, '(\d{4}-\d{2}-\d{2})\.json\.gz$', 1) AS DATE) AS snapshot_date,
        events
    FROM {{ source('fpl_raw', 'bootstrap') }}
),

latest AS (
    SELECT events
    FROM files
    ORDER BY snapshot_date DESC
    LIMIT 1
)

SELECT
    CAST(e.id AS BIGINT) AS gameweek,
    e.finished AND e.data_checked AS is_final,
    CAST(e.most_captained AS BIGINT) AS most_captained_player_id
FROM (SELECT unnest(events) AS e FROM latest)