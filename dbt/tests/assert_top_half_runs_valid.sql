-- Fails if the counts contradict each other: more top-half weeks than weeks played,
-- a longest run longer than all top-half weeks, or a current run longer than the longest.
SELECT *
FROM {{ ref('mart_top_half_weeks') }}
WHERE top_half_weeks > gameweeks_played
    OR longest_run > top_half_weeks
    OR current_run > longest_run