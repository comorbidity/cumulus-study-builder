CREATE TABLE {{ prefix }}__cohort_casedef_exclude AS
-- Optional: user defined exclusions. Edit this template to add exclusion
-- criteria (return subject_ref rows to exclude), then regenerate casedef.
SELECT
    cast(NULL as varchar) as subject_ref,
    cast(NULL as varchar) as encounter_ref,
    cast(NULL as varchar) as exclude_reason,
    cast(NULL as varchar) as fhir_resource
WHERE FALSE;
