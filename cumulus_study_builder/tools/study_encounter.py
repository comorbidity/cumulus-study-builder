from pathlib import Path
from cumulus_study_builder.tools import (
    manifest,
    template,
    fhir_reference
)

#-----------------------------------------------------------------------------
# List of study encounter tables.
#
# cohort_study_period       = patient encounters specified by "include_study_period"
# encounter               = one row per retained encounter_ref
# encounter_{Reference}   = linked FHIR resources; see
# `tools.fhir_reference.Aspect`. The `_enc` table contains multivalued encounter
# coding metadata and may have multiple rows per encounter_ref.
#-----------------------------------------------------------------------------
STUDY_PERIOD = 'cohort_study_period'
ENCOUNTER = 'encounter'
OBS_TABLES = ['encounter_obs_base', 'encounter_lab_base']

def make_study_encounter(table_list:list) -> list[Path]:
    return [template.copy(f"{table}.sql") for table in table_list]

def make() -> list[Path]:
    """
    Study Encounter is built from the "template/" directory. It contains all
    encounters matching the study-period, demographic, and utilization criteria,
    plus linked FHIR resources.
    """
    file_upload = manifest.FileAction(
        file_list=['../spreadsheet/file_upload_encounter.toml'],
        description='inclusion/exclusion criteria for study encounters',
        build_type='build:parallel')

    study_period = make_study_encounter([STUDY_PERIOD])
    study_encounter = make_study_encounter([ENCOUNTER])
    obs_tables = make_study_encounter(OBS_TABLES)
    aspect_list = fhir_reference.list_aspect()
    aspect_tables = [f"{ENCOUNTER}_{aspect}" for aspect in aspect_list]
    aspect_tables = make_study_encounter(aspect_tables)

    actions = [
        file_upload,
        manifest.SqlAction(study_period, 'study_period'),
        manifest.SqlAction(study_encounter, 'study_encounter'),
        manifest.SqlAction(obs_tables, 'obs_base, lab_base', build_type='build:serial'),
        manifest.SqlAction(aspect_tables, f'study_encounter aspects {str(aspect_list)}'),
    ]

    return [manifest.save_actions_toml(actions, 'study_encounter.toml')]

if __name__ == '__main__':
    for manifest_toml in make():
        print(manifest_toml)
