-- eligible_timeline. episode-level ANALYSIS SPINE for survival / TTE / PSM.
--
-- Grain. one row per line-forming therapy episode (time zero = index_date). It
-- fixes the pieces that must not vary across analyses. the analysis unit, time
-- zero, exposure, anchor context, demographics as of index, the outcome
-- time-to-event / censoring fields, and baseline observability. Baseline
-- COVARIATES are deliberately NOT materialized here. assemble them downstream by
-- joining this spine to the dated {{ prefix }}__cohort_variable_wide_<aspect>
-- tables, windowing each variable by its own date strictly before index_date to
-- avoid leakage. see the eligible skill for the covariate-assembly template.
CREATE  TABLE   {{ prefix }}__eligible_timeline AS
WITH
base AS (
    SELECT  e.subject_ref,
            e.rx_class,
            e.rx_therapy_line_number,
            e.rx_event_anchor_date          AS index_date,
            e.casedef_date_best,
            e.casedef_date_best_subtype,
            e.rx_days_since_casedef          AS days_casedef_to_index,
            e.outcome_date_first,
            e.outcome_has_qualifying,
            e.is_outcome_risk_set_eligible_bool
    FROM    {{ prefix }}__eligible AS e
    WHERE   e.rx_is_line_forming
),
-- demographics as of index. the closest encounter on or before index_date.
demographics AS (
    SELECT  b.subject_ref, b.index_date,
            t.age_at_visit, t.gender, t.race_display, t.ethnicity_display,
            t.encounter_ref                 AS demographics_encounter_ref,
            t.enc_period_start_day          AS demographics_date,
            ROW_NUMBER() OVER (
                PARTITION BY b.subject_ref, b.index_date
                ORDER BY t.enc_period_start_day DESC
            ) AS rn
    FROM    base AS b
    JOIN    {{ prefix }}__cohort_timeline AS t
      ON    t.subject_ref = b.subject_ref
     AND    t.enc_period_start_day <= b.index_date
),
-- last observed encounter end on or after index. loss-to-follow-up censor date.
last_enc AS (
    SELECT  b.subject_ref, b.index_date,
            MAX(COALESCE(t.enc_period_end_day, t.enc_period_start_day)) AS last_encounter_date
    FROM    base AS b
    JOIN    {{ prefix }}__cohort_timeline AS t
      ON    t.subject_ref = b.subject_ref
     AND    COALESCE(t.enc_period_end_day, t.enc_period_start_day) >= b.index_date
    GROUP BY b.subject_ref, b.index_date
),
-- baseline observability. encounters in [index - 365, index).
baseline AS (
    SELECT  b.subject_ref, b.index_date,
            COUNT(DISTINCT t.encounter_ref)         AS baseline_encounter_count,
            MIN(t.enc_period_start_day)             AS baseline_observation_start_date
    FROM    base AS b
    JOIN    {{ prefix }}__cohort_timeline AS t
      ON    t.subject_ref = b.subject_ref
     AND    t.enc_period_start_day <  b.index_date
     AND    t.enc_period_start_day >= DATE_ADD('day', -365, b.index_date)
    GROUP BY b.subject_ref, b.index_date
)
SELECT  b.subject_ref,
        b.rx_class,
        b.rx_therapy_line_number,
        b.index_date,                                       -- time zero
        --
        b.casedef_date_best,
        b.casedef_date_best_subtype,                        -- provenance only
        b.days_casedef_to_index,
        --
        d.age_at_visit,
        d.gender,
        d.race_display,
        d.ethnicity_display,
        d.demographics_encounter_ref,
        d.demographics_date,
        --
        -- outcome + censoring
        b.is_outcome_risk_set_eligible_bool                 AS outcome_risk_set_eligible_bool,
        (b.outcome_date_first IS NOT NULL
         AND b.outcome_date_first > b.index_date)           AS outcome_event_bool,
        CASE WHEN b.outcome_date_first IS NOT NULL AND b.outcome_date_first > b.index_date
             THEN 1 ELSE 0 END                              AS outcome_event_observed,
        b.outcome_date_first,
        CASE WHEN b.outcome_date_first IS NOT NULL AND b.outcome_date_first > b.index_date
             THEN b.outcome_date_first
             ELSE l.last_encounter_date END                 AS outcome_analysis_end_date,
        DATE_DIFF('day', b.index_date,
             CASE WHEN b.outcome_date_first IS NOT NULL AND b.outcome_date_first > b.index_date
                  THEN b.outcome_date_first
                  ELSE l.last_encounter_date END)           AS days_to_outcome_or_censor,
        l.last_encounter_date,
        --
        -- baseline observability (covariates assembled externally, see skill)
        365                                                 AS baseline_lookback_days,
        COALESCE(bl.baseline_encounter_count, 0)            AS baseline_encounter_count,
        bl.baseline_observation_start_date,
        DATE_DIFF('day', bl.baseline_observation_start_date, b.index_date)
                                                            AS baseline_observation_span_days
FROM    base AS b
LEFT JOIN demographics AS d ON d.subject_ref = b.subject_ref AND d.index_date = b.index_date AND d.rn = 1
LEFT JOIN last_enc     AS l ON l.subject_ref = b.subject_ref AND l.index_date = b.index_date
LEFT JOIN baseline     AS bl ON bl.subject_ref = b.subject_ref AND bl.index_date = b.index_date
;
