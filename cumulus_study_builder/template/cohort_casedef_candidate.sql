CREATE TABLE {{ prefix }}__cohort_casedef_candidate AS
WITH encounter_evidence AS (
    SELECT 'casedef_dx'     AS valueset,
            dx_system       AS system,
            dx_code         AS code,
            condition_ref   AS resource_ref,
            subject_ref,
            {{ encounter_ref }}
    FROM    {{ prefix }}__encounter_dx
    WHERE   dx_system IS NOT NULL AND dx_code IS NOT NULL
    UNION ALL
    SELECT 'casedef_rx', rx_system, rx_code, medicationrequest_ref, subject_ref, {{ encounter_ref }}
    FROM    {{ prefix }}__encounter_rx
    WHERE   rx_system IS NOT NULL AND rx_code IS NOT NULL
    UNION ALL
    SELECT 'casedef_proc', proc_system, proc_code, procedure_ref, subject_ref, {{ encounter_ref }}
    FROM    {{ prefix }}__encounter_proc
    WHERE   proc_system IS NOT NULL AND proc_code IS NOT NULL
    UNION ALL
    SELECT 'casedef_lab', lab_observation_system, lab_observation_code, observation_ref, subject_ref, {{ encounter_ref }}
    FROM    {{ prefix }}__encounter_lab
    WHERE   lab_observation_system IS NOT NULL AND lab_observation_code IS NOT NULL
    UNION ALL
    SELECT 'casedef_diag', diag_system, diag_code, diagnosticreport_ref, subject_ref, {{ encounter_ref }}
    FROM    {{ prefix }}__encounter_diag
    WHERE   diag_system IS NOT NULL AND diag_code IS NOT NULL
    UNION ALL
    SELECT 'casedef_doc', doc_type_system, doc_type_code, documentreference_ref, subject_ref, {{ encounter_ref }}
    FROM    {{ prefix }}__encounter_doc
    WHERE   doc_type_system IS NOT NULL AND doc_type_code IS NOT NULL
),
encounter_evidence_distinct AS (
    SELECT DISTINCT valueset, system, code, resource_ref, subject_ref, {{ encounter_ref }}
    FROM encounter_evidence
)
SELECT  p.valueset,
        casedef.*,
        p.resource_ref,
        p.subject_ref,
        p.{{ encounter_ref }}
FROM    encounter_evidence_distinct AS p
JOIN    {{ prefix }}__valueset_casedef  AS casedef
        ON  casedef.system = p.system
        AND casedef.code   = p.code
;
