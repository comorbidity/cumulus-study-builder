CREATE  TABLE   {{ prefix }}__encounter_diag AS
WITH
-- Priority A: encounter_ref maps to a retained encounter row
by_encounter AS (
    SELECT
            diag.status                     AS diag_status,
            diag.category_system            AS diag_category_system,
            diag.category_code              AS diag_category_code,
            diag.category_display           AS diag_category_display,
            diag.code_system                AS diag_system,
            diag.code_code                  AS diag_code,
            diag.code_display               AS diag_display,
            diag.effectivedatetime_day      AS diag_effectivedatetime_day,
            diag.effectiveperiod_start_day  as diag_effectiveperiod_start_day,
            diag.aux_has_text               AS aux_has_text,
            diag.diagnosticreport_ref       AS diagnosticreport_ref,
            diag.subject_ref                AS subject_ref,
            diag.encounter_ref              AS encounter_ref,
            diag.encounter_ref              AS encounter_ref_link,
            'encounter_ref'                 AS encounter_ref_link_col
    FROM    {{ prefix }}__encounter   AS enc
    JOIN    core__diagnosticreport                  AS diag
    ON      enc.encounter_ref = diag.encounter_ref
    AND     enc.subject_ref   = diag.subject_ref
    WHERE   diag.encounter_ref IS NOT NULL
),

-- Priority B candidates: effectivedatetime present AND the report's encounter_ref is
-- NOT a retained encounter row. The anti-join against
-- encounter covers BOTH a true-null encounter_ref (never matches) and
-- an encounter_ref pointing at an encounter dropped by the study-encounter filters.
-- NOTE: anti-join depends on consistent subject_ref formatting across the two tables.
date_candidates AS (
    SELECT  DISTINCT
            diag.diagnosticreport_ref,
            diag.subject_ref,
            diag.effectivedatetime_day      AS candidate_day
    FROM    core__diagnosticreport          AS diag
    LEFT JOIN {{ prefix }}__encounter AS enc
    ON      diag.encounter_ref = enc.encounter_ref
    AND     diag.subject_ref   = enc.subject_ref
    WHERE   diag.effectivedatetime_day  IS NOT  NULL
    AND     enc.encounter_ref            IS      NULL
),
date_candidates_ranked AS (
    SELECT
            diag.diagnosticreport_ref,
            enc.encounter_ref AS encounter_ref_link,
            ROW_NUMBER() OVER (
                PARTITION BY diag.diagnosticreport_ref
                ORDER BY
                    -- Tie-Break #1: encounter starts on the date-mapped day
                    CASE
                        WHEN diag.candidate_day = enc.enc_period_start_day
                        THEN 0 ELSE 1
                    END,
                    -- Tie-Break #2: narrowest window
                    DATE_DIFF(
                        'day',
                        enc.enc_period_start_day,
                        enc.enc_period_end_day_filled
                    ) ASC,
                    -- Tie-Break #3: start closest to the date-mapped day
                    ABS(
                        DATE_DIFF(
                            'day',
                            enc.enc_period_start_day,
                            diag.candidate_day
                        )
                    ) ASC,
                    -- Tie-Break #4: encounter ordinal
                    enc.enc_period_ordinal ASC,
                    -- Tie-Break #5: encounter_ref
                    enc.encounter_ref ASC
            ) AS link_rank
    FROM    date_candidates AS diag
    JOIN    {{ prefix }}__encounter AS enc
    ON      enc.subject_ref = diag.subject_ref
    AND     diag.candidate_day BETWEEN enc.enc_period_start_day AND enc.enc_period_end_day_filled
),
date_candidates_links AS (
    SELECT  diagnosticreport_ref,
            encounter_ref_link
    FROM    date_candidates_ranked
    WHERE   link_rank = 1
),
by_date AS (
    SELECT
            diag.status                     AS diag_status,
            diag.category_system            AS diag_category_system,
            diag.category_code              AS diag_category_code,
            diag.category_display           AS diag_category_display,
            diag.code_system                AS diag_system,
            diag.code_code                  AS diag_code,
            diag.code_display               AS diag_display,
            diag.effectivedatetime_day      AS diag_effectivedatetime_day,
            diag.effectiveperiod_start_day  as diag_effectiveperiod_start_day,
            diag.aux_has_text               AS aux_has_text,
            diag.diagnosticreport_ref       AS diagnosticreport_ref,
            diag.subject_ref                AS subject_ref,
            diag.encounter_ref              AS encounter_ref,
            link.encounter_ref_link         AS encounter_ref_link,
            'effective_date'                AS encounter_ref_link_col
    FROM    date_candidates_links           AS link
    JOIN    core__diagnosticreport          AS diag
    ON      diag.diagnosticreport_ref       = link.diagnosticreport_ref
    WHERE   diag.effectivedatetime_day      IS NOT  NULL
),
union_link AS (
    SELECT * FROM by_encounter
    UNION ALL
    SELECT * FROM by_date
),
-- diag-specific enrichment #1: LOINC consumer name + include_diag_category display.
hydrate AS (
    SELECT  COALESCE(valueset.display, union_link.diag_category_display, 'NONE') AS diag_category_display_best,
            CASE
                WHEN union_link.diag_system = 'http://loinc.org'
                THEN loinc.consumer_name.consumer_name
                ELSE union_link.diag_display
            END AS diag_display_best,
            union_link.*
    FROM    union_link
    LEFT JOIN loinc.consumer_name
    ON      union_link.diag_code = loinc.consumer_name.loinc_number
    LEFT JOIN {{ prefix }}__include_diag_category AS valueset
    ON      union_link.diag_category_code = valueset.code
)
SELECT  DISTINCT
        hydrate.*
FROM    hydrate
;
