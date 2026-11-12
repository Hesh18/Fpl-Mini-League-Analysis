-- Fails if a manager's season total isn't the sum of gameweek points minus transfer hits.
WITH latest AS (
    SELECT manager_id, total_points
    FROM {{ ref('stg_manager_gameweeks') }}
    QUALIFY row_number() OVER (PARTITION BY manager_id ORDER BY gameweek DESC) = 1
),

computed AS (
    SELECT manager_id, sum(points) - sum(transfer_cost) AS computed_total
    FROM {{ ref('stg_manager_gameweeks') }}
    GROUP BY manager_id
)

SELECT l.manager_id, l.total_points, c.computed_total
FROM latest AS l
JOIN computed AS c ON c.manager_id = l.manager_id
WHERE l.total_points <> c.computed_total