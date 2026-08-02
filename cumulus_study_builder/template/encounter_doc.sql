CREATE  TABLE   {{ prefix }}__encounter_doc AS
WITH
-- Priority A: encounter_ref maps to a retained encounter row
by_encounter AS (
    SELECT
            doc.docstatus               AS doc_status,
            doc.type_code               AS doc_type_code,
            doc.type_display            AS doc_type_display,
            doc.type_system             AS doc_type_system,
            doc.author_day              AS doc_author_day,
            doc."date"                  AS doc_date,
            COALESCE(doc.author_day,DATE(doc."date"))
                                        AS doc_link_day,
            doc.aux_has_text            AS aux_has_text,
            doc.documentreference_ref   AS documentreference_ref,
            doc.subject_ref             AS subject_ref,
            doc.encounter_ref           AS encounter_ref,
            doc.encounter_ref           AS encounter_ref_link,
            'encounter_ref'             AS encounter_ref_link_col
    FROM    {{ prefix }}__encounter AS enc
    JOIN    core__documentreference     AS doc
    ON      enc.subject_ref      = doc.subject_ref
    AND     enc.encounter_ref    = doc.encounter_ref
    WHERE   doc.encounter_ref   IS NOT NULL
),

-- Priority B candidates: date present AND the document's encounter_ref is NOT a
-- retained encounter row. The anti-join against
-- encounter covers BOTH a true-null encounter_ref (never matches) and
-- an encounter_ref pointing at an encounter dropped by the study-encounter filters.
-- NOTE: anti-join depends on consistent subject_ref formatting across the two tables.
date_candidates AS (
    SELECT  DISTINCT
            doc.documentreference_ref,
            doc.subject_ref,
            COALESCE(doc.author_day,DATE(doc."date"))
                                            AS doc_day
    FROM    core__documentreference         AS doc
    LEFT JOIN {{ prefix }}__encounter AS enc
    ON      doc.encounter_ref = enc.encounter_ref
    AND     doc.subject_ref   = enc.subject_ref
    WHERE   COALESCE(doc.author_day,DATE(doc."date"))   IS NOT  NULL
    AND     enc.encounter_ref                            IS      NULL
),
date_candidates_ranked AS (
    SELECT  doc.documentreference_ref,
            enc.encounter_ref AS encounter_ref_link,
            ROW_NUMBER() OVER (
                PARTITION BY doc.documentreference_ref
                ORDER BY
                    -- Tie-Break #1: encounter starts on the date-mapped day
                    CASE
                        WHEN doc.doc_day = enc.enc_period_start_day
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
                            doc.doc_day
                        )
                    ) ASC,
                    -- Tie-Break #4: encounter ordinal
                    enc.enc_period_ordinal ASC,
                    -- Tie-Break #5: encounter_ref
                    enc.encounter_ref ASC
            ) AS doc_link_rank
    FROM    date_candidates AS doc
    JOIN    {{ prefix }}__encounter AS enc
    ON      enc.subject_ref = doc.subject_ref
    AND     doc.doc_day BETWEEN enc.enc_period_start_day AND enc.enc_period_end_day_filled
),
date_candidates_links AS (
    SELECT  documentreference_ref,
            encounter_ref_link
    FROM date_candidates_ranked
    WHERE doc_link_rank = 1
),
by_date AS (
    SELECT
            doc.docstatus               AS doc_status,
            doc.type_code               AS doc_type_code,
            doc.type_display            AS doc_type_display,
            doc.type_system             AS doc_type_system,
            doc.author_day              AS doc_author_day,
            doc."date"                  AS doc_date,
            COALESCE(doc.author_day,DATE(doc."date"))
                                        AS doc_link_day,
            doc.aux_has_text            AS aux_has_text,
            doc.documentreference_ref   AS documentreference_ref,
            doc.subject_ref             AS subject_ref,
            doc.encounter_ref           AS encounter_ref,
            link.encounter_ref_link     AS encounter_ref_link,
            'document_date'             AS encounter_ref_link_col
    FROM    date_candidates_links AS link
    JOIN    core__documentreference AS doc
    ON      doc.documentreference_ref = link.documentreference_ref
    WHERE   COALESCE(doc.author_day,DATE(doc."date")) IS NOT NULL
),
union_link AS (
    SELECT * FROM by_encounter
    UNION ALL
    SELECT * from by_date
)
SELECT  DISTINCT
        union_link.*
FROM    union_link
;
