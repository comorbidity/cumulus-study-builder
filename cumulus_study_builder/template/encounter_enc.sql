CREATE  TABLE   {{ prefix }}__encounter_enc AS
SELECT  DISTINCT
        -- Encounter class.
        core_enc.class_system        AS enc_class_system,
        core_enc.class_code          AS enc_class_code,
        core_enc.class_display       AS enc_class_display,

        -- Encounter service type.
        core_enc.servicetype_system  AS enc_servicetype_system,
        core_enc.servicetype_code    AS enc_servicetype_code,
        core_enc.servicetype_display AS enc_servicetype_display,

        -- Encounter type.
        core_enc.type_system         AS enc_type_system,
        core_enc.type_code           AS enc_type_code,
        core_enc.type_display        AS enc_type_display,

        -- Encounter priority.
        core_enc.priority_system     AS enc_priority_system,
        core_enc.priority_code       AS enc_priority_code,
        core_enc.priority_display    AS enc_priority_display,

        -- Reason for visit.
        core_enc.reasoncode_system   AS enc_reasoncode_system,
        core_enc.reasoncode_code     AS enc_reasoncode_code,
        core_enc.reasoncode_display  AS enc_reasoncode_display,

        -- Discharge disposition.
        core_enc.dischargedisposition_system  AS enc_dischargedisposition_system,
        core_enc.dischargedisposition_code    AS enc_dischargedisposition_code,
        core_enc.dischargedisposition_display AS enc_dischargedisposition_display,

        -- Calendar rollups.
        core_enc.period_start_week   AS enc_period_start_week,
        core_enc.period_start_month  AS enc_period_start_month,
        core_enc.period_start_year   AS enc_period_start_year,

        enc.*
FROM    {{ prefix }}__encounter AS enc
JOIN    core__encounter        AS core_enc
ON      enc.encounter_ref = core_enc.encounter_ref
;
