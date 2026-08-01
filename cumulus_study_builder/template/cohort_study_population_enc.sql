CREATE  TABLE   {{ prefix }}__cohort_study_population_enc AS
SELECT DISTINCT
        enc.priority_system     AS enc_priority_system,
        enc.priority_code       AS enc_priority_code,
        enc.priority_display    AS enc_priority_display,

        enc.reasoncode_system   AS enc_reasoncode_system,
        enc.reasoncode_code     AS enc_reasoncode_code,
        enc.reasoncode_display  AS enc_reasoncode_display,

        enc.dischargedisposition_system     AS enc_dischargedisposition_system,
        enc.dischargedisposition_code       AS enc_dischargedisposition_code,
        enc.dischargedisposition_display    AS enc_dischargedisposition_display,

        enc.period_start_week   AS enc_period_start_week,
        enc.period_start_month  AS enc_period_start_month,
        enc.period_start_year   AS enc_period_start_year,

        study_population.*
FROM    {{ prefix }}__cohort_study_population   AS study_population
JOIN    core__encounter                         AS enc
ON      study_population.encounter_ref = enc.encounter_ref
;
