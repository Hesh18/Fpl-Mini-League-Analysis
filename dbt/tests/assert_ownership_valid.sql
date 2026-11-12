-- Fails if ownership is missing, not a number, or outside 0-100%.
SELECT snapshot_date, player_id, player_name, selected_by_pct
FROM {{ ref('stg_player_snapshots') }}
WHERE selected_by_pct IS NULL OR selected_by_pct NOT BETWEEN 0 AND 100