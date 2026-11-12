-- One row per manager per snapshot day: the mini-league table.
WITH files AS (
    SELECT
        CAST(regexp_extract(filename, '(\d{4}-\d{2}-\d{2})\.json\.gz$', 1) AS DATE) AS snapshot_date,
        standings
    FROM read_json('{{ raw_dir }}/league/*.json.gz', filename = true, union_by_name = true)
),

rows AS (
    SELECT snapshot_date, unnest(standings.results) AS r
    FROM files
)

SELECT
    snapshot_date,
    r.entry AS manager_id,
    r.entry_name AS team_name,
    r.rank AS league_rank,
    r.total AS total_points,
    r.event_total AS gameweek_points
FROM rows