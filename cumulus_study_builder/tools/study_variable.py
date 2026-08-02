from pathlib import Path
from cumulus_study_builder.tools import filetool, tablespace, manifest, fhir_reference
from cumulus_study_builder.tools.fhir_reference import Aspect, get_aspect

#-----------------------------------------------------------------------------
# List variables
#-----------------------------------------------------------------------------
def list_variables(aspect: str | Aspect = None) -> list[str]:
    if not aspect:
        return _list_variables()
    elif isinstance(aspect, str):
        aspect = Aspect[aspect]
    return [v for v in _list_variables() if get_aspect(v) == aspect]

def _list_variables() -> list[str]:
    """
    List of valueset variable names (not including the "case definition").
    The case definition (casedef) is authored/generated separately by casedef.py.
    """
    var_list = filetool.filter_aspect(filetool.list_spreadsheet())
    var_list = [v.name for v in var_list]
    var_list = [v for v in var_list if "casedef" not in v]
    var_list = [filetool.file_to_simplename(v) for v in var_list]
    return sorted(list(set(var_list)))

def list_variables_as_str(variable_list:list[str], quote="'", seperator=',') -> str:
    return tablespace.sql_quote(variable_list, quote, seperator)

def list_variable_uploads() -> list[Path]:
    return filetool.filter_aspect(filetool.list_spreadsheet())

#-----------------------------------------------------------------------------
# Aspect(s) for Variable
#-----------------------------------------------------------------------------
def list_aspect_names() -> list[str]:
    return [aspect.name for aspect in list_aspects()]

def list_aspects() -> list[Aspect]:
    return list(dict_aspects().keys())

def dict_aspects() -> dict[Aspect, list[str]]:
    out = {}
    for variable in list_variables():
        aspect = get_aspect(variable)
        if aspect not in out.keys():
            out[aspect] = [variable]
        else:
            out[aspect].append(variable)
    return out

#-----------------------------------------------------------------------------
# List tables
#-----------------------------------------------------------------------------
def list_tables() -> list[str]:
    return list_tables_valueset() + list_tables_cohort()

def list_tables_valueset() -> list[str]:
    return [tablespace.name_valueset(v) for v in list_variables()]

def list_tables_cohort() -> list[str]:
    return [tablespace.name_cohort(v) for v in list_variables()]

def list_files() -> list[Path]:
    return [filetool.path_athena(file) for file in list_tables_cohort()]

#-----------------------------------------------------------------------------
# Cohort variable JOIN encounter evidence
#-----------------------------------------------------------------------------
def make_cohort(variable: str) -> Path:
    col = fhir_reference.get_column(variable)
    encounter = tablespace.name_encounter(col.aspect.name)
    valueset_name = tablespace.name_valueset(variable)
    cohort_name = tablespace.name_cohort(variable)
    where = [f'{encounter}.{col.code} = {valueset_name}.code',
             f'{encounter}.{col.system} = {valueset_name}.system']
    sql = tablespace.ctas(encounter, variable, where)
    return filetool.save_athena_view(cohort_name, sql)

#-----------------------------------------------------------------------------
# Make
#-----------------------------------------------------------------------------
def make() -> list[Path]:
    upload_file = 'file_upload_study_variable.toml'
    upload_list = list_variable_uploads()
    variable_list = [make_cohort(variable) for variable in list_variables()]

    actions_list = [manifest.FileAction(file_list=[f'../spreadsheet/{upload_file}'],
                                        description='CSV valueset definitions for variables',
                                        build_type='build:parallel'),
                    manifest.SqlAction(file_list=variable_list,
                                       description='variable cohorts')]

    return [manifest.save_file_upload_toml(upload_list, upload_file),
            manifest.save_actions_toml(actions_list, 'study_variable.toml')]

if __name__ == '__main__':
    for output_toml in make():
        print(output_toml)
