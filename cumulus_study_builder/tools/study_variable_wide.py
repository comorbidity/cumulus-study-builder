from pathlib import Path
from cumulus_study_builder.tools.settings import ENCOUNTER_REF
from cumulus_study_builder.tools import filetool, tablespace, manifest, template
from cumulus_study_builder.tools.fhir_reference import Aspect
from cumulus_study_builder.tools.tablespace import name_trim, name_cohort
from cumulus_study_builder.tools.study_variable import (
    list_variables,
    list_variables_as_str,
    list_aspects,
)

#-----------------------------------------------------------------------------
# RECONSTRUCTED (approximate) — replaced by the source `study_variable_wide.py`
# on device sync.
#
# Builds the multi-variable UNION and WIDE (pivoted) representations of the
# study variables:
#   cohort_variable_union            (all variables, long form)
#   cohort_variable_union_<aspect>   (joined back to encounter_<aspect>)
#   cohort_variable_wide             (boolean pivot, one column per variable)
#   cohort_variable_wide_<aspect>    (per-aspect column-group pivot)
#
# The union generation below matches the source. The WIDE per-aspect pivot
# (select_wide_dict: IF(variable='x', <col>) AS x_<col>) is study-column-specific
# and is best copied verbatim from your source study.
#-----------------------------------------------------------------------------

# --- UNION -------------------------------------------------------------------
def make_variable_union_bool() -> list[Path]:
    return [_make_variable_union(aspect=None)]

def make_variable_union_aspect() -> list[Path]:
    return [_make_variable_union(aspect=aspect) for aspect in list_aspects()]

def _make_variable_union(aspect: Aspect = None) -> Path:
    cohort = f'variable_union_{aspect.name}' if aspect else 'variable_union'
    variable_list = list_variables(aspect)
    return filetool.save_athena_view(
        name_cohort(cohort),
        template.load(f"cohort_{cohort}.sql",
                      encounter_ref=ENCOUNTER_REF,
                      select_union=select_union(variable_list),
                      variable_list=list_variables_as_str(variable_list)))

def select_union(variable_list: list[str]) -> str:
    sql = list()
    for variable in variable_list:
        variable = name_trim(variable)
        cohort = name_cohort(variable)
        select = (f"\tSELECT '{variable}'\t AS variable, code, display, system, "
                  f"resource_ref, {ENCOUNTER_REF}\n\tFROM {cohort}")
        sql.append(select)
    return "\n\tUNION ALL\n".join(sql)

# --- WIDE --------------------------------------------------------------------
def make_variable_wide_bool() -> list[Path]:
    variable_list = list_variables()
    return [filetool.save_athena_view(
        name_cohort('variable_wide'),
        template.load('cohort_variable_wide.sql',
                      encounter_ref=ENCOUNTER_REF,
                      select_wide_bool=select_wide_bool(variable_list),
                      select_wide_any=select_wide_any(variable_list)))]

def make_variable_wide_aspect() -> list[Path]:
    return [_make_variable_wide_aspect(aspect) for aspect in list_aspects()]

def _make_variable_wide_aspect(aspect: Aspect) -> Path:
    variable_list = list_variables(aspect)
    return filetool.save_athena_view(
        name_cohort(f'variable_wide_{aspect.name}'),
        template.load('cohort_variable_wide_aspect.sql',
                      aspect=aspect.name,
                      encounter_ref=ENCOUNTER_REF,
                      select_wide_dict=select_wide_dict(aspect, variable_list)))

def select_wide_bool(variable_list: list[str]) -> str:
    cols = [f"MAX(CASE WHEN variable = '{name_trim(v)}' THEN true ELSE false END) AS {name_trim(v)}"
            for v in variable_list]
    return ',\n'.join(cols) if cols else 'NULL AS _empty'

def select_wide_any(variable_list: list[str]) -> str:
    cols = [f"BOOL_OR({name_trim(v)}) AS {name_trim(v)}" for v in variable_list]
    return ',\n'.join(cols) if cols else 'NULL AS _empty'

def select_wide_dict(aspect: Aspect, variable_list: list[str]) -> str:
    # NOTE: source study emits IF(variable='x', <aspect date/status/ref cols>) AS x_<col>.
    # This reconstruction emits a minimal ref pivot; copy the source for full columns.
    cols = [f"IF(variable = '{name_trim(v)}', resource_ref) AS {name_trim(v)}_ref"
            for v in variable_list]
    return ',\n'.join(cols) if cols else 'NULL AS _empty'

# --- MAKE --------------------------------------------------------------------
def make() -> list[Path]:
    union_bool = make_variable_union_bool()
    union_aspect = make_variable_union_aspect()
    wide_bool = make_variable_wide_bool()
    wide_aspect = make_variable_wide_aspect()
    actions = [
        manifest.SqlAction(union_bool, 'variable union (bool)'),
        manifest.SqlAction(union_aspect, "variable union (per aspect)"),
        manifest.SqlAction(wide_bool, 'variable wide (bool)'),
        manifest.SqlAction(wide_aspect, 'variable wide (per aspect)'),
    ]
    return [manifest.save_actions_toml(actions, 'study_variable_wide.toml')]

if __name__ == '__main__':
    for target in make():
        print(target)
