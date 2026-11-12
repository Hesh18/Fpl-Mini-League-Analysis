-- Fails if the newest player snapshot is more than 2 days old: data has stopped arriving.
SELECT
    max(snapshot_date) AS latest_snapshot,
    current_date - max(snapshot_date) AS days_old
FROM stg_player_snapshots
HAVING coalesce(current_date - max(snapshot_date), 999) > 2