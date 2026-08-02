CREATE  TABLE   {{ prefix }}__encounter AS
WITH
-- Candidate encounters after study-period and demographic filters. Encounter
-- class, service type, type, priority, reason, and discharge disposition are
-- intentionally excluded here because they may be multivalued. They live in
-- encounter_enc.
encounter_candidate AS (
    SELECT  enc.status,
            enc.age_at_visit,
            valueset_age_group.age_group,
            enc.gender,
            enc.race_display,
            enc.ethnicity_display,
            sp.period_ordinal       AS enc_period_ordinal,
            enc.period_start_day    AS enc_period_start_day,
            enc.period_end_day      AS enc_period_end_day,
            COALESCE(enc.period_end_day, enc.period_start_day)
                                    AS enc_period_end_day_filled,
            enc.subject_ref,
            enc.encounter_ref
    FROM    core__encounter                     AS enc
    JOIN    {{ prefix }}__cohort_study_period   AS sp
    ON      enc.encounter_ref = sp.encounter_ref
    JOIN    {{ prefix }}__include_gender        AS gender_include
    ON      enc.gender = gender_include.code
    JOIN    {{ prefix }}__include_age_at_visit  AS age_include
    ON      enc.age_at_visit BETWEEN age_include.age_min AND age_include.age_max
    JOIN    {{ prefix }}__valueset_age_group    AS valueset_age_group
    ON      enc.age_at_visit = valueset_age_group.age_at_visit
    WHERE   enc.encounter_ref IS NOT NULL
),
-- Guarantee the base-table grain even when core__encounter contains multiple
-- rows for the same encounter_ref. The ordering is deterministic; exact ties
-- are equivalent after the multivalued coding columns have been removed.
encounter_ranked AS (
    SELECT  encounter_candidate.*,
            ROW_NUMBER() OVER (
                PARTITION BY encounter_ref
                ORDER BY
                    enc_period_start_day      ASC NULLS LAST,
                    enc_period_end_day_filled ASC NULLS LAST,
                    subject_ref               ASC,
                    status                    ASC NULLS LAST,
                    age_at_visit              ASC NULLS LAST,
                    gender                    ASC NULLS LAST,
                    race_display              ASC NULLS LAST,
                    ethnicity_display         ASC NULLS LAST,
                    age_group                 ASC NULLS LAST,
                    enc_period_ordinal        ASC NULLS LAST
            ) AS encounter_row_num
    FROM    encounter_candidate
),
encounter AS (
    SELECT  status,
            age_at_visit,
            age_group,
            gender,
            race_display,
            ethnicity_display,
            enc_period_ordinal,
            enc_period_start_day,
            enc_period_end_day,
            enc_period_end_day_filled,
            subject_ref,
            encounter_ref
    FROM    encounter_ranked
    WHERE   encounter_row_num = 1
),
utilization AS (
    SELECT  COUNT(DISTINCT enc_period_ordinal) AS cnt_period,
            subject_ref
    FROM    encounter
    GROUP BY subject_ref
),
duration AS (
    SELECT  MIN(enc_period_start_day)        AS min_start_day,
            MAX(enc_period_end_day_filled)   AS max_end_day,
            subject_ref
    FROM    encounter
    GROUP BY subject_ref
),
duration_days AS (
    SELECT  subject_ref,
            min_start_day,
            max_end_day,
            DATE_DIFF('day', min_start_day, max_end_day) AS cnt_days
    FROM    duration
)
SELECT  encounter.*
FROM    encounter
JOIN    utilization
ON      encounter.subject_ref = utilization.subject_ref
JOIN    duration_days
ON      encounter.subject_ref = duration_days.subject_ref
WHERE   EXISTS (
            SELECT  1
            FROM    {{ prefix }}__include_utilization AS utilization_include
            WHERE   utilization.cnt_period
                    BETWEEN utilization_include.enc_min AND utilization_include.enc_max
            AND     duration_days.cnt_days
                    BETWEEN utilization_include.days_min AND utilization_include.days_max
        )
;
