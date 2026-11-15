-- Fails if a manager-gameweek appears twice, or a captain "lost" a negative number of points.
SELECT manager_id, gameweek, count(*) AS row_count, min(captain_points_lost) AS lowest_points_lost
FROM {{ ref('mart_captain_decisions') }}
GROUP BY manager_id, gameweek
HAVING count(*) > 1
    OR min(captain_points_lost) < 0