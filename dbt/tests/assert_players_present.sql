-- Fails if any day's snapshot file has fewer than 500 players, including zero.
WITH files AS (
    SELECT CAST(regexp_extract(file, '(\d{4}-\d{2}-\d{2})\.json\.gz$', 1) AS DATE) AS snapshot_date
    FROM glob('{{ env_var('FPL_RAW_DIR', '../data/snapshots/raw') }}/bootstrap/*.json.gz')
)

SELECT f.snapshot_date, count(p.player_id) AS players
FROM files AS f
LEFT JOIN {{ ref('stg_player_snapshots') }} AS p ON p.snapshot_date = f.snapshot_date
GROUP BY f.snapshot_date
HAVING count(p.player_id) < 500