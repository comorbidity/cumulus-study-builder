-- RECONSTRUCTED. standard Cumulus study-metadata date range. overlay source via SYNC.md.
CREATE  TABLE   {{ prefix }}__meta_date AS
SELECT  MIN(enc_period_start_day)                               AS min_date,
        MAX(COALESCE(enc_period_end_day, enc_period_start_day)) AS max_date
FROM    {{ prefix }}__encounter
;
