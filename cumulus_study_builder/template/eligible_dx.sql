-- eligible_dx. best case/index (anchor) date per subject.
--
-- This is the generic "best evidence for the casedef match date". For IBD the
-- anchor is the diagnosis-established date. for a procedure-defined study
-- (e.g. kidney transplant) the anchor is the procedure date. The date is the
-- FIRST case-defining encounter (casedef_period = 'peri', days_since = 0) from
-- {{ prefix }}__cohort_casedef, restricted to the strongest tier and broken by
-- subtype specificity. Adapt the ladder to your study (add an LLM rung, change
-- the tier rule) in the study-builder. see the eligible skill.
CREATE  TABLE   {{ prefix }}__eligible_dx AS
WITH
-- FHIR rung. the first case-defining encounter for each subject.
fhir_anchor AS (
    SELECT  subject_ref,
            enc_period_start_day        AS anchor_date,
            tier,
            subtype,
            system,
            code,
            display,
            resource_ref,
            encounter_ref,
            ROW_NUMBER() OVER (
                PARTITION BY subject_ref
                ORDER BY
                    tier ASC,                       -- strongest (tier 1) evidence first
                    enc_period_start_day ASC,       -- earliest establishing encounter
                    -- subtype specificity tie-break. more specific subtypes first.
                    CASE subtype
                        WHEN 'IBD_NOS' THEN 3
                        WHEN 'IBDU'    THEN 2
                        ELSE 0
                    END ASC,
                    resource_ref ASC
            ) AS rn
    FROM    {{ prefix }}__cohort_casedef
    WHERE   casedef_period = 'peri'
    AND     enc_period_start_day IS NOT NULL
)
--
-- OPTIONAL LLM rung. when a chart-review 'diagnosis' (or procedure) task exists,
-- UNION a stronger-priority row sourced from {{ prefix }}__llm_timeline here and
-- let the COALESCE/priority pick it. left out by default so the template renders
-- and runs without an LLM stage. see the eligible skill for the ladder pattern.
--
SELECT  subject_ref,
        anchor_date                     AS casedef_date_best,
        'FHIR_CASEDEF_FIRST_ENCOUNTER'  AS casedef_date_best_source,
        1                               AS casedef_date_best_source_priority,
        tier                            AS casedef_date_best_tier,
        subtype                         AS casedef_date_best_subtype,  -- provenance of the anchor only
        system                          AS casedef_date_best_system,
        code                            AS casedef_date_best_code,
        display                         AS casedef_date_best_display,
        resource_ref                    AS casedef_date_best_ref,
        encounter_ref                   AS casedef_date_best_encounter_ref,
        (anchor_date IS NOT NULL)       AS has_casedef_date_best_bool
FROM    fhir_anchor
WHERE   rn = 1
;
