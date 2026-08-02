-- eligible_outcome. the subject's FIRST qualifying outcome event (time-to-event).
--
-- Grain. one row per subject in {{ prefix }}__eligible_dx_date (every eligible subject
-- appears, outcome or not). The default outcome is any procedure-aspect event
-- (variable LIKE 'proc%'), matching the IBD "first qualifying surgery" pattern.
-- Repoint WHERE to your outcome valueset (an outcome study-variable, or a dx/proc
-- subset) per the eligible skill. earliest qualifying event wins.
CREATE  TABLE   {{ prefix }}__eligible_outcome AS
WITH outcome_events AS (
    SELECT  u.subject_ref,
            u.enc_period_start_day  AS outcome_date,
            u.variable              AS outcome_type,
            u.resource_ref          AS outcome_ref,
            u.system                AS outcome_system,
            u.code                  AS outcome_code,
            ROW_NUMBER() OVER (
                PARTITION BY u.subject_ref
                ORDER BY u.enc_period_start_day ASC, u.resource_ref ASC
            ) AS rn
    FROM    {{ prefix }}__cohort_variable_union AS u
    WHERE   u.variable LIKE 'proc%'                 -- <-- your outcome valueset
    AND     u.enc_period_start_day IS NOT NULL
),
first_outcome AS (
    SELECT subject_ref, outcome_date, outcome_type, outcome_ref, outcome_system, outcome_code
    FROM   outcome_events WHERE rn = 1
)
SELECT  dx.subject_ref,
        (o.outcome_date IS NOT NULL)    AS outcome_has_qualifying,
        o.outcome_date                  AS outcome_date_first,
        o.outcome_type                  AS outcome_type_first,
        'variable_union'                AS outcome_source_first,
        o.outcome_ref                   AS outcome_evidence_ref_first
FROM    {{ prefix }}__eligible_dx_date AS dx
LEFT JOIN first_outcome AS o ON o.subject_ref = dx.subject_ref
;
