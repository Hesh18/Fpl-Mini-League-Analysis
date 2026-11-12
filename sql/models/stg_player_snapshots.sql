-- One row per player per snapshot day, with clean types and real units.
WITH files AS (
    SELECT
        CAST(regexp_extract(filename, '(\d{4}-\d{2}-\d{2})\.json\.gz$', 1) AS DATE) AS snapshot_date,
        elements
    FROM read_json('{{ raw_dir }}/bootstrap/*.json.gz', filename = true, union_by_name = true)
),

players AS (
    SELECT snapshot_date, unnest(elements) AS p
    FROM files
)

SELECT
    snapshot_date,
    p.id AS player_id,
    p.web_name AS player_name,
    p.team AS team_id,
    CASE p.element_type
        WHEN 1 THEN 'GKP'
        WHEN 2 THEN 'DEF'
        WHEN 3 THEN 'MID'
        WHEN 4 THEN 'FWD'
    END AS position,
    p.now_cost / 10.0 AS price_m,
    TRY_CAST(p.selected_by_percent AS DOUBLE) AS selected_by_pct,
    p.status,
    TRY_CAST(p.chance_of_playing_next_round AS INTEGER) AS chance_of_playing_next_round,
    TRY_CAST(p.form AS DOUBLE) AS form,
    p.total_points,
    p.minutes,
    TRY_CAST(p.expected_goals AS DOUBLE) AS expected_goals,
    TRY_CAST(p.expected_assists AS DOUBLE) AS expected_assists,
    p.news
FROM players