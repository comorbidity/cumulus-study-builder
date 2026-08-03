-- Canonical sample-stage template (absorbed from the ibd-cds source study,
-- adapted to the encounter paradigm: cohort_study_population* -> encounter*).
CREATE TABLE {{ prefix }}__sample_casedef_{{ temporality }}_limit_note_{{ limit }} as
SELECT  DISTINCT
        subject_ref, note_ordinal, days_since, note_ref, group_name
FROM
        {{ prefix }}__sample_casedef_{{ temporality }}
WHERE
        note_ordinal <= {{ limit }}
ORDER BY
        subject_ref, note_ordinal;