from pathlib import Path
from cumulus_study_builder.tools.settings import ENCOUNTER_REF
from cumulus_study_builder.tools import filetool, template, tablespace, manifest
from cumulus_study_builder.tools.study_variable import list_aspect_names

#-----------------------------------------------------------------------------
# RECONSTRUCTED (approximate) — replaced by the source `sample.py` on device sync.
#
# Sampling selects clinical notes (FHIR DiagnosticReport + DocumentReference)
# for chart review, keyed to the case definition and organized by encounter
# timing relative to the first case-defining encounter:
#   pre = before, peri = during, peri_post = during-or-after, post = after
#
# The chart-review (LLM) stage runs over these samples. This starter renders the
# sample_casedef* templates; the source study additionally emits per-temporality
# note/patient LIMIT variants and a fully-shaped sample.toml — bring those over
# from your source study if you need them.
#-----------------------------------------------------------------------------
TEMPORALITY = ['pre', 'peri', 'peri_post', 'post']

def make_sample() -> list[Path]:
    return [template.copy('sample_casedef.sql', encounter_ref=ENCOUNTER_REF)]

def make_aspect() -> list[Path]:
    return [_make_aspect(aspect) for aspect in list_aspect_names()]

def _make_aspect(aspect: str) -> Path:
    content = template.load('sample_casedef_aspect.sql', aspect=aspect, encounter_ref=ENCOUNTER_REF)
    table = tablespace.name_prefix(f'sample_casedef_{aspect}')
    return filetool.save_athena(f'{table}.sql', content)

def make_temporality() -> list[Path]:
    out = []
    for temporality in TEMPORALITY:
        content = template.load('sample_casedef_temporality.sql',
                                temporality=temporality, encounter_ref=ENCOUNTER_REF)
        table = tablespace.name_prefix(f'sample_casedef_{temporality}')
        out.append(filetool.save_athena(f'{table}.sql', content))
    return out

def make() -> list[Path]:
    sample_files = make_sample()
    aspect_files = make_aspect()
    temporality_files = make_temporality()
    actions = [
        manifest.FileAction([f'../spreadsheet/file_upload_casedef.toml']),
        manifest.SqlAction(sample_files, 'sample casedef notes'),
        manifest.SqlAction(aspect_files, 'sample casedef notes per aspect'),
        manifest.SqlAction(temporality_files, 'sample casedef notes per temporality'),
    ]
    return [manifest.save_actions_toml(actions, 'sample.toml')]

if __name__ == '__main__':
    for target in make():
        print(target)
