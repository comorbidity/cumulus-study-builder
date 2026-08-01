-- RECONSTRUCTED. base clinical-note sample for chart review. selects DiagnosticReport
-- + DocumentReference notes for the case cohort, tagged with casedef timing. The
-- source sample.py emits a richer sampler (per-temporality note/patient LIMIT
-- variants). overlay the exact source via SYNC.md.
CREATE  TABLE   {{ prefix }}__sample_casedef AS
WITH notes AS (
    SELECT  'diag'                          AS note_aspect,
            diag.diagnosticreport_ref       AS note_ref,
            diag.diag_effectivedatetime_day AS note_day,
            diag.subject_ref,
            diag.{{ encounter_ref }}
    FROM    {{ prefix }}__cohort_study_population_diag AS diag
    WHERE   diag.aux_has_text = 1
    UNION ALL
    SELECT  'doc',
            doc.documentreference_ref,
            doc.doc_link_day,
            doc.subject_ref,
            doc.{{ encounter_ref }}
    FROM    {{ prefix }}__cohort_study_population_doc AS doc
    WHERE   doc.aux_has_text = 1
)
SELECT  DISTINCT
        notes.note_aspect,
        notes.note_ref,
        notes.note_day,
        casedef.casedef_period,
        casedef.days_since      AS casedef_days_since,
        casedef.ordinal_since   AS casedef_ordinal_since,
        casedef.resource_ref    AS casedef_ref,
        notes.subject_ref,
        notes.{{ encounter_ref }}
FROM    notes
JOIN    {{ prefix }}__cohort_casedef AS casedef
ON      notes.{{ encounter_ref }} = casedef.{{ encounter_ref }}
;
