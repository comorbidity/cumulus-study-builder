-- DERIVED from cohort_variable_union_dx.sql (aspect=proc). overlay exact source via SYNC.md.
CREATE  TABLE   {{ prefix }}__cohort_variable_union_proc AS
SELECT DISTINCT
        var.variable,
        var.code,
        var.display,
        var.system,
        proc.*
FROM    {{ prefix }}__cohort_variable_union         AS var
JOIN    {{ prefix }}__encounter_proc    AS proc
ON      var.resource_ref = proc.procedure_ref
AND     var.system = proc.proc_system
AND     var.code = proc.proc_code
WHERE   var.variable IN
(
 {{ variable_list }}
);
