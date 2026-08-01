-- RECONSTRUCTED. per-aspect note sample. overlay source via SYNC.md.
CREATE  TABLE   {{ prefix }}__sample_casedef_{{ aspect }} AS
SELECT  DISTINCT sample.*
FROM    {{ prefix }}__sample_casedef                      AS sample
JOIN    {{ prefix }}__cohort_study_population_{{ aspect }} AS aspect
ON      sample.{{ encounter_ref }} = aspect.{{ encounter_ref }}
;
