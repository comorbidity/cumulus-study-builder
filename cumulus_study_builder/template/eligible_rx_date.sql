-- eligible_rx_date. treatment-class first-exposure dates and therapy lines.
--
-- Grain. one row per subject x rx_class. rx_class is the rx-aspect study-variable
-- name authored via the study-variable skill (variable names starting 'rx').
-- rx_sequence_date = first observed exposure for the class. rx_therapy_line_number
-- = dense rank of class first-dates within the subject (1 = first line). The IBD
-- study closes/reopens episodes from LLM failure evidence (response, ADE). that
-- episode engine is study-specific. extend this per the eligible skill.
CREATE  TABLE   {{ prefix }}__eligible_rx_date AS
WITH
rx_events AS (
    SELECT  u.subject_ref,
            u.variable                          AS rx_class,
            u.enc_period_start_day              AS rx_event_date,
            u.resource_ref,
            u.code,
            u.system
    FROM    {{ prefix }}__cohort_variable_union AS u
    WHERE   u.variable LIKE 'rx%'                -- rx-aspect variables only
    AND     u.enc_period_start_day IS NOT NULL
),
rx_first AS (
    SELECT  subject_ref,
            rx_class,
            MIN(rx_event_date)                  AS rx_sequence_date,
            COUNT(DISTINCT resource_ref)        AS rx_evidence_row_count,
            ARBITRARY(resource_ref)             AS rx_first_evidence_ref
    FROM    rx_events
    GROUP BY subject_ref, rx_class
),
dx AS (
    SELECT subject_ref, casedef_date_best FROM {{ prefix }}__eligible_dx_date
)
SELECT  f.subject_ref,
        f.rx_class,
        f.rx_sequence_date,
        f.rx_sequence_date                      AS rx_event_anchor_date,   -- time zero for this line
        DENSE_RANK() OVER (
            PARTITION BY f.subject_ref
            ORDER BY f.rx_sequence_date ASC
        )                                       AS rx_therapy_line_number,
        dx.casedef_date_best,
        DATE_DIFF('day', dx.casedef_date_best, f.rx_sequence_date)
                                                AS rx_days_since_casedef,
        f.rx_evidence_row_count,
        f.rx_first_evidence_ref,
        TRUE                                    AS rx_is_line_forming      -- refine per study (e.g. exclude steroids)
FROM    rx_first AS f
LEFT JOIN dx ON dx.subject_ref = f.subject_ref
;
