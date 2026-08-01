-- RECONSTRUCTED. per-temporality note sample ({{ temporality }} relative to the
-- first case-defining encounter. peri_post = peri OR post). overlay source via SYNC.md.
CREATE  TABLE   {{ prefix }}__sample_casedef_{{ temporality }} AS
SELECT  DISTINCT sample.*
FROM    {{ prefix }}__sample_casedef AS sample
WHERE   ('{{ temporality }}' =  'peri_post' AND sample.casedef_period IN ('peri','post'))
   OR   ('{{ temporality }}' <> 'peri_post' AND sample.casedef_period =  '{{ temporality }}')
;
