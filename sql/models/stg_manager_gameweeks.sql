-- One row per manager per gameweek, taken from the newest snapshot that has it.
WITH files AS (
    SELECT
        CAST(regexp_extract(filename, '(\d+)_\d{4}-\d{2}-\d{2}\.json\.gz$', 1) AS BIGINT) AS manager_id,
        CAST(regexp_extract(filename, '(\d{4}-\d{2}-\d{2})\.json\.gz$', 1) AS DATE) AS snapshot_date,
        current
    FROM read_json('{{ raw_dir }}/manager_history/*.json.gz', filename = true, union_by_name = true)
),

gameweeks AS (
    SELECT manager_id, snapshot_date, unnest(current) AS gw
    FROM files
)

SELECT
    manager_id,
    gw.event AS gameweek,
    gw.points,
    gw.total_points,
    gw.overall_rank,
    gw.bank / 10.0 AS bank_m,
    gw.value / 10.0 AS squad_value_m,
    gw.event_transfers AS transfers,
    gw.event_transfers_cost AS transfer_cost,
    gw.points_on_bench,
    snapshot_date
FROM gameweeks
QUALIFY row_number() OVER (PARTITION BY manager_id, gameweek ORDER BY snapshot_date DESC) = 1