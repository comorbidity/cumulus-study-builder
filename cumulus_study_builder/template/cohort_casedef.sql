CREATE  TABLE   {{ prefix }}__cohort_casedef AS
WITH
-- casedef matches for encounter_ref
casedef_encounter AS (
    SELECT  DISTINCT
            enc.age_at_visit,
            enc.age_group,
            enc.enc_period_start_day,
            enc.enc_period_ordinal,
            casedef.*
    FROM    {{ prefix }}__cohort_casedef_include    AS casedef
    JOIN    {{ prefix }}__encounter   AS enc
    ON      casedef.subject_ref = enc.subject_ref
    AND     casedef.{{ encounter_ref }} = enc.encounter_ref
),
-- rare use of select DISTINCT for query optimization
casedef_subject AS (
    SELECT  DISTINCT
            subject_ref
    FROM    casedef_encounter
),
-- history of subject_ref
history AS (
    SELECT  enc.enc_period_ordinal,
            enc.enc_period_start_day,
            enc.age_at_visit,
            enc.age_group,
            enc.gender,
            enc.race_display,
            enc.status,
            enc.subject_ref,
            enc.encounter_ref
    FROM    casedef_subject
    JOIN    {{ prefix }}__encounter as enc
    ON      casedef_subject.subject_ref = enc.subject_ref
),
-- min/max age and periods for subject_ref
calc_duration as (
    SELECT  min(age_at_visit) as age_at_casedef_min,
            max(age_at_visit) as age_at_casedef_max,
            min(enc_period_ordinal)  as enc_period_ordinal_min,
            min(enc_period_start_day) as enc_period_start_day_min,
            subject_ref
    FROM    casedef_encounter
    GROUP BY subject_ref
),
-- days between: *1st* encounter_ref and *this* encounter_ref
calc_days_since as (
    SELECT  date_diff(
                'day',
                DATE(calc_duration.enc_period_start_day_min),
                DATE(history.enc_period_start_day)) as days_since,
            (history.enc_period_ordinal - enc_period_ordinal_min) as ordinal_since,
            history.encounter_ref
    FROM    history
    JOIN    calc_duration
    ON      history.subject_ref = calc_duration.subject_ref
),
-- AUTHORED TAIL (see DRAFT_NOTES / SYNC.md. the source file was only partially
-- recoverable this session. this completion is faithful to the documented casedef
-- model and renders. overlay the exact source cohort_casedef.sql via SYNC.md).
-- per-subject case identity (subtype, tier, ... and the case-defining resource).
casedef_match AS (
    SELECT  DISTINCT
            {%- for col in casedef_columns %}
            {{ col }},
            {%- endfor %}
            resource_ref,
            subject_ref
    FROM    casedef_encounter
)
SELECT  DISTINCT
        calc_days_since.days_since,
        calc_days_since.ordinal_since,
        CASE
            WHEN calc_days_since.days_since < 0 THEN 'pre'
            WHEN calc_days_since.days_since = 0 THEN 'peri'
            ELSE 'post'
        END                                     AS casedef_period,
        -- casedef columns from CSV Valueset
        {%- for col in casedef_columns %}
        casedef_match.{{ col }},
        {%- endfor %}
        --
        casedef_match.resource_ref,
        history.age_at_visit,
        history.age_group,
        history.gender,
        history.race_display,
        history.status,
        history.enc_period_start_day,
        history.enc_period_ordinal,
        history.subject_ref,
        history.encounter_ref,
        history.encounter_ref                   AS encounter_ref_link
FROM    calc_days_since
JOIN    history
ON      calc_days_since.encounter_ref = history.encounter_ref
JOIN    casedef_match
ON      history.subject_ref = casedef_match.subject_ref
;
