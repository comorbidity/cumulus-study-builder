CREATE      TABLE   {{ prefix }}__cohort_timeline AS
SELECT      DISTINCT
            (wide.encounter_ref_link IS NOT NULL)      AS variable_wide_bool,
            (casedef.encounter_ref_link IS NOT NULL)   AS casedef_bool,
            -- casedef columns from CSV valueset.
            {%- for col in casedef_columns %}
            casedef.{{ col }},
            {%- endfor %}
            casedef.days_since                    AS casedef_days_since,
            casedef.ordinal_since                 AS casedef_ordinal_since,
            casedef.resource_ref                  AS casedef_ref,
            enc.enc_period_start_day,
            enc.enc_period_end_day,
            enc.enc_period_ordinal,
            enc.age_at_visit,
            enc.gender,
            enc.race_display,
            enc.ethnicity_display,
            enc.encounter_ref,
            enc.subject_ref
FROM        {{ prefix }}__encounter AS enc
LEFT JOIN   {{ prefix }}__cohort_casedef         AS casedef
ON          enc.encounter_ref = casedef.encounter_ref_link
LEFT JOIN   {{ prefix }}__cohort_variable_wide   AS wide
ON          enc.encounter_ref = wide.encounter_ref_link
;
