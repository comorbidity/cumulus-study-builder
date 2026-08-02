CREATE  TABLE   {{ prefix }}__cohort_variable_union AS
WITH
select_union AS
(
{{ select_union }}
),
evidence_distinct AS
(
    SELECT  select_union.variable,
            select_union.code,
            MAX(CAST(select_union.display AS VARCHAR)) AS display,
            select_union.system,
            select_union.resource_ref,
            select_union.{{ encounter_ref }}
    FROM    select_union
    GROUP BY
            select_union.variable,
            select_union.code,
            select_union.system,
            select_union.resource_ref,
            select_union.{{ encounter_ref }}
)
SELECT  DISTINCT
        evidence_distinct.variable,
        evidence_distinct.code,
        evidence_distinct.display,
        evidence_distinct.system,
        evidence_distinct.resource_ref,
        evidence_distinct.{{ encounter_ref }},
        enc.subject_ref,
        enc.status,
        enc.age_at_visit,
        enc.age_group,
        enc.gender,
        enc.race_display,
        enc.ethnicity_display,
        enc.enc_period_ordinal,
        enc.enc_period_start_day,
        enc.enc_period_end_day
FROM    evidence_distinct
JOIN    {{ prefix }}__encounter AS enc
ON      evidence_distinct.{{ encounter_ref }} = enc.encounter_ref
;
