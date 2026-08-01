-- eligible_rx_date_evidence. one row per supporting resource for a class episode.
--
-- Normalized provenance for {{ prefix }}__eligible_rx_date. use this table to
-- search or join the underlying MedicationRequest/Dispense (or LLM) references
-- rather than unpacking an array. one row per (subject, rx_class, resource_ref).
CREATE  TABLE   {{ prefix }}__eligible_rx_date_evidence AS
SELECT  DISTINCT
        u.subject_ref,
        u.variable          AS rx_class,
        u.resource_ref      AS rx_evidence_ref,
        u.enc_period_start_day AS rx_evidence_date,
        u.system            AS rx_evidence_system,
        u.code              AS rx_evidence_code,
        u.display           AS rx_evidence_display
FROM    {{ prefix }}__cohort_variable_union AS u
WHERE   u.variable LIKE 'rx%'
AND     u.resource_ref IS NOT NULL
;
