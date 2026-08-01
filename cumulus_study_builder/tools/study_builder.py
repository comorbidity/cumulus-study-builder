from pathlib import Path
from cumulus_study_builder.tools import (
    study_population,
    study_variable,
    study_variable_wide,
    casedef,
    sample,
    eligible,
    cube_fhir,
    study_meta,
)

def make_study() -> list[Path]:
    """
    Regenerate every stage's submanifest TOML (and rendered athena SQL) in one
    pass. This is the SPINE: run it after editing any stage's inputs (the
    include_* CSVs, valueset CSVs, casedef.csv, or the Pydantic models), then
    run `cumulus-library build`.
    """
    return (study_population.make() +
            study_variable.make() +
            study_variable_wide.make() +
            casedef.make() +
            sample.make() +
            eligible.make() +
            cube_fhir.make() +
            study_meta.make())

if __name__ == '__main__':
    for manifest_toml in make_study():
        print(manifest_toml)
    # Optional: regenerate the data-quality test manifest if tests/ is present.
    try:
        from tests import test_athena_data_quality
        print(test_athena_data_quality.make())
    except Exception as exc:  # pragma: no cover - tests are optional in the starter
        print(f"(skipping test manifest regeneration: {exc})")
