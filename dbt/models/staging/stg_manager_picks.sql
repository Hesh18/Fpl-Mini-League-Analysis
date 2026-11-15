-- One row per manager, gameweek and squad player: the 15 picks for each final gameweek.
WITH files AS (
    SELECT
        CAST(regexp_extract(filename, '(\d+)_\d+\.json\.gz$', 1) AS BIGINT) AS manager_id,
        CAST(regexp_extract(filename, '_(\d+)\.json\.gz$', 1) AS BIGINT) AS gameweek,
        active_chip,
        automatic_subs,
        picks
    FROM {{ source('fpl_raw', 'manager_picks') }}
),

picks AS (
    SELECT manager_id, gameweek, active_chip, unnest(picks) AS p
    FROM files
),

subs AS (
    SELECT manager_id, gameweek, unnest(automatic_subs) AS s
    FROM files
)

SELECT
    picks.manager_id,
    picks.gameweek,
    picks.p.element AS player_id,
    picks.p.position AS squad_position,
    picks.p.multiplier,
    picks.p.is_captain,
    picks.p.is_vice_captain,
    picks.active_chip AS chip,
    sub_in.manager_id IS NOT NULL AS auto_subbed_in,
    sub_out.manager_id IS NOT NULL AS auto_subbed_out,
    (picks.p.position <= 11 AND sub_in.manager_id IS NULL) OR sub_out.manager_id IS NOT NULL AS picked_to_start
FROM picks
LEFT JOIN subs AS sub_in
    ON sub_in.manager_id = picks.manager_id
    AND sub_in.gameweek = picks.gameweek
    AND sub_in.s.element_in = picks.p.element
LEFT JOIN subs AS sub_out
    ON sub_out.manager_id = picks.manager_id
    AND sub_out.gameweek = picks.gameweek
    AND sub_out.s.element_out = picks.p.element