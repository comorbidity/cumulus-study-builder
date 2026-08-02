from pathlib import Path
from cumulus_study_builder.tools import manifest, study_meta
from cumulus_study_builder.tools.cube import PREFIX
from cumulus_study_builder.tools.cube import (
    cube_patient,
    cube_encounter,
    cube_note,
    cube_document,
    cube_diagnostic
)
#-----------------------------------------------------------------------------
# cube = optional aggregate/count "cube" tables for dashboards/export.
#
# TEMPLATE NOTE (RECONSTRUCTED STUB): the source study builds FHIR cube tables
# here. This starter ships a no-op so `study_builder.make_study()` runs. Replace
# with the source `cube_fhir.py` (and cube.py / cube_llm.py) if you want the cube
# stage, or author your own aggregate/export tables. See cumulus-library docs on
# `export:counts` and PSM/cube builders.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Study Encounters
#-----------------------------------------------------------------------------
def make_study_encounter() -> list[Path]:
    return [
        # encounters for study population
        cube_encounter(source_table=f'{PREFIX}__encounter_enc',
                       table_cols=['age_group',
                                   'age_at_visit',
                                   'enc_period_start_year',
                                   'enc_class_display',
                                   'enc_type_display',
                                   'enc_servicetype_display']),

        # patients for study population
        cube_patient(source_table=f'{PREFIX}__encounter',
                     table_cols=['age_group',
                                 'gender',
                                 'race_display']),

        # Diagnosis
        cube_patient(source_table=f'{PREFIX}__encounter_dx',
                     table_cols=['dx_clinical_status',
                                 'dx_verification_status',
                                 'dx_category_code',
                                 'dx_system',
                                 'dx_code',
                                 'dx_display']),

        # Allergy
        cube_patient(source_table=f'{PREFIX}__encounter_allergy',
                     table_cols=['allergy_category',
                                 'allergy_criticality',
                                 'allergy_display',
                                 'allergy_manifestation_display']),

        # Medications
        cube_patient(source_table=f'{PREFIX}__encounter_rx',
                     table_cols=['rx_status',
                                 'rx_category_code',
                                 'rx_system',
                                 'rx_code',
                                 'rx_display']),

        # Procedures
        cube_patient(source_table=f'{PREFIX}__encounter_proc',
                     table_cols=['proc_status',
                                 'proc_category_display',
                                 'proc_system',
                                 'proc_code',
                                 'proc_display']),

        # Lab Observations
        cube_patient(source_table=f'{PREFIX}__encounter_lab',
                     table_cols=['lab_status',
                                 'lab_observation_system',
                                 'lab_observation_code',
                                 'lab_observation_display']),

        # Documents
        cube_patient(source_table=f'{PREFIX}__encounter_doc',
                     table_cols=['doc_status',
                                 'doc_type_display',
                                 'aux_has_text']),

        cube_document(source_table=f'{PREFIX}__encounter_doc',
                      table_cols=['doc_status',
                                  'doc_type_code',
                                  'doc_type_display',
                                  'aux_has_text']),

        # Diagnostic Reports
        cube_patient(source_table=f'{PREFIX}__encounter_diag',
                     table_cols=['diag_category_display_best',
                                 'diag_system',
                                 'diag_code',
                                 'diag_display',
                                 'aux_has_text']),

        cube_diagnostic(source_table=f'{PREFIX}__encounter_diag',
                        table_cols=['diag_category_display_best',
                                    'diag_system',
                                    'diag_code',
                                    'diag_display',
                                    'aux_has_text']),
    ]

#-----------------------------------------------------------------------------
# Case Definition
#-----------------------------------------------------------------------------
def make_casedef() -> list[Path]:
    return [
        # Count patients for casedef
        cube_patient(source_table=f'{PREFIX}__cohort_casedef',
                     table_cols=['age_at_casedef_min',
                                 'age_group',
                                 'gender',
                                 'system',
                                 'code',
                                 'display']),

        # DX Diagnoses
        cube_patient(source_table=f'{PREFIX}__cohort_casedef_dx',
                     table_cols=['variable',
                                 'dx_category_code',
                                 'dx_code',
                                 'dx_system',
                                 'dx_display']),

        # RX Medications
        cube_patient(source_table=f'{PREFIX}__cohort_casedef_rx',
                     table_cols=['variable',
                                 'rx_category_code',
                                 'rx_status',
                                 'rx_code',
                                 'rx_display']),

        # Lab Observations
        cube_patient(source_table=f'{PREFIX}__cohort_casedef_lab',
                     table_cols=['variable',
                                 'lab_observation_system',
                                 'lab_observation_code',
                                 'lab_observation_display']),

        # Procedures
        cube_patient(source_table=f'{PREFIX}__cohort_casedef_proc',
                     table_cols=['variable',
                                 'proc_category_display',
                                 'proc_system',
                                 'proc_code',
                                 'proc_display']),
    ]

#-----------------------------------------------------------------------------
# Variables (coded vars matching FHIR resource)
#-----------------------------------------------------------------------------
def make_variable_union() -> list[Path]:
    return [
        cube_patient(source_table=f'{PREFIX}__cohort_variable_union',
                     table_cols=['age_group',
                                 'variable',
                                 'code',
                                 'system',
                                 'display',]),
    ]

#-----------------------------------------------------------------------------
# Make
#-----------------------------------------------------------------------------
def make() -> list[Path]:
    study_population_sql_list = make_study_encounter()
    casedef_sql_list = make_casedef()
    variable_sql_list = make_variable_union()

    actions = [
        manifest.SqlAction(study_population_sql_list, 'SQL cube study population'),
        manifest.SqlAction(variable_sql_list, 'SQL cube variable union'),
        manifest.SqlAction(casedef_sql_list, 'SQL cube casedef'),
        manifest.ExportAction(study_population_sql_list, 'export cube tables study populations'),
        manifest.ExportAction(variable_sql_list, 'export cube tables variable union'),
        manifest.ExportAction(casedef_sql_list, 'export cube tables casedef'),
    ]
    actions.reverse() # fail fast and get more interesting results earlier
    actions.extend(study_meta.make_actions())

    return [manifest.save_actions_toml(actions, 'cube.toml')]

#-----------------------------------------------------------------------------
# MAIN method
#-----------------------------------------------------------------------------
if __name__ == '__main__':
    for target in make():
        print(target)
