-- One row per Premier League team, from the most recent snapshot.
WITH files AS (
    SELECT
        CAST(regexp_extract(filename, '(\d{4}-\d{2}-\d{2})\.json\.gz$', 1) AS DATE) AS snapshot_date,
        teams
    FROM {{ source('fpl_raw', 'bootstrap') }}
),

latest AS (
    SELECT teams
    FROM files
    ORDER BY snapshot_date DESC
    LIMIT 1
)

SELECT
    t.id AS team_id,
    t.name AS team_name,
    t.short_name AS team_short_name
FROM (SELECT unnest(teams) AS t FROM latest)