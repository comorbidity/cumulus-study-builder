-- eligible. event-level eligibility and outcome risk-set membership.
--
-- Grain. one row per therapy-line episode from {{ prefix }}__eligible_rx_date,
-- joined per subject to the anchor date ({{ prefix }}__eligible_dx_date) and left to
-- the first outcome ({{ prefix }}__eligible_outcome). Risk-set flags are
-- evaluated at each line's anchor. A line at or after the first outcome stays in
-- the history but is not outcome-free. This is the CDS / cohort-selection surface.
CREATE  TABLE   {{ prefix }}__eligible AS
SELECT  rx.subject_ref,
        rx.rx_class,
        rx.rx_therapy_line_number,
        rx.rx_sequence_date,
        rx.rx_event_anchor_date,
        rx.rx_days_since_casedef,
        rx.rx_is_line_forming,
        --
        dx.casedef_date_best,
        dx.casedef_date_best_subtype,
        dx.has_casedef_date_best_bool,
        --
        COALESCE(o.outcome_has_qualifying, FALSE)   AS outcome_has_qualifying,
        o.outcome_date_first,
        o.outcome_type_first,
        --
        -- risk set. outcome-free at this anchor when there is no outcome or the
        -- outcome is strictly after the anchor. same-day outcome is NOT outcome-free.
        (o.outcome_date_first IS NULL OR o.outcome_date_first > rx.rx_event_anchor_date)
                                                    AS outcome_free_at_anchor_bool,
        (o.outcome_date_first = rx.rx_event_anchor_date) AS outcome_on_anchor_date_bool,
        DATE_DIFF('day', rx.rx_event_anchor_date, o.outcome_date_first)
                                                    AS days_anchor_to_outcome,
        (rx.rx_is_line_forming
         AND (o.outcome_date_first IS NULL OR o.outcome_date_first > rx.rx_event_anchor_date))
                                                    AS is_outcome_risk_set_eligible_bool,
        CASE
            WHEN NOT rx.rx_is_line_forming THEN 'non_line_forming_treatment_history'
            WHEN o.outcome_date_first IS NOT NULL
                 AND o.outcome_date_first <= rx.rx_event_anchor_date
                 THEN 'outcome_at_or_before_anchor_history_only'
            ELSE 'eligible_outcome_risk_set'
        END                                         AS event_disposition
FROM    {{ prefix }}__eligible_rx_date AS rx
JOIN    {{ prefix }}__eligible_dx_date AS dx ON dx.subject_ref = rx.subject_ref
LEFT JOIN {{ prefix }}__eligible_outcome AS o ON o.subject_ref = rx.subject_ref
;
