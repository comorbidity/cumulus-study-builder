from pathlib import Path
from cumulus_study_builder.tools import manifest

#-----------------------------------------------------------------------------
# cube = optional aggregate/count "cube" tables for dashboards/export.
#
# TEMPLATE NOTE (RECONSTRUCTED STUB): the source study builds FHIR cube tables
# here. This starter ships a no-op so `study_builder.make_study()` runs. Replace
# with the source `cube_fhir.py` (and cube.py / cube_llm.py) if you want the cube
# stage, or author your own aggregate/export tables. See cumulus-library docs on
# `export:counts` and PSM/cube builders.
#-----------------------------------------------------------------------------
def make() -> list[Path]:
    return [manifest.save_actions_toml([], 'cube.toml')]

if __name__ == '__main__':
    for target in make():
        print(target)
