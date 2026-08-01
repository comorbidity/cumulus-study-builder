from pathlib import Path
from cumulus_study_builder.tools import (
    manifest,
    template,
    fhir_reference
)

#-----------------------------------------------------------------------------
# List of study population tables.
#
# cohort_study_period       = patient encounters specified by "include_study_period"
# cohort_study_population    = patient encounters with additional metadata
# cohort_study_population_{Reference} = see `tools.fhir_reference.Aspect`
#-----------------------------------------------------------------------------
STUDY_PERIOD = 'cohort_study_period'
STUDY_POPULATION = 'cohort_study_population'
OBS_TABLES = ['cohort_study_population_obs_base', 'cohort_study_population_lab_base']

def make_study_population(table_list:list) -> list[Path]:
    return [template.copy(f"{table}.sql") for table in table_list]

def make() -> list[Path]:
    """
    Study Population is built from the "template/" dir. It contains all patient
    encounters matching inclusion criteria and the linked FHIR resources.
    """
    file_upload = manifest.FileAction(
        file_list=['../spreadsheet/file_upload_population.toml'],
        description='inclusion/exclusion criteria for study population',
        build_type='build:parallel')

    study_period = make_study_population([STUDY_PERIOD])
    study_population = make_study_population([STUDY_POPULATION])
    obs_tables = make_study_population(OBS_TABLES)
    aspect_list = fhir_reference.list_aspect()
    aspect_tables = [f"{STUDY_POPULATION}_{aspect}" for aspect in aspect_list]
    aspect_tables = make_study_population(aspect_tables)

    actions = [
        file_upload,
        manifest.SqlAction(study_period, 'study_period'),
        manifest.SqlAction(study_population, 'study_population'),
        manifest.SqlAction(obs_tables, 'obs_base, lab_base', build_type='build:serial'),
        manifest.SqlAction(aspect_tables, f'study_population aspects {str(aspect_list)}'),
    ]

    return [manifest.save_actions_toml(actions, 'study_population.toml')]

if __name__ == '__main__':
    for manifest_toml in make():
        print(manifest_toml)
