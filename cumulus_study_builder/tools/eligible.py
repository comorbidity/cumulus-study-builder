from pathlib import Path
from cumulus_study_builder.tools import manifest, template, filetool, tablespace

#-----------------------------------------------------------------------------
# eligible = the computable-phenotype / analytic layer for target-trial
# emulation (TTE), clinical decision support (CDS), and patient matching.
#
# TWO parts (the "templates + guided" model. see the `eligible` skill):
#
# 1. A GENERIC template family, rendered from template/eligible_*.sql into
#    athena/<prefix>__eligible_*.sql (below). It resolves the best case/index
#    (casedef match) date, sequences treatment classes into therapy lines,
#    resolves a first time-to-event outcome, evaluates outcome risk-set
#    eligibility, and emits an analysis spine (index/time-zero, exposure,
#    demographics-as-of-index, outcome + censoring, baseline observability) for
#    KM / Cox / PSM. These CTAS tables are the tabular inputs for downstream
#    Python / pandas analysis. Adapt them to your study per the eligible skill.
#
# 2. Optional STUDY-AUTHORED cohort-selection views. hand-write
#    athena/<prefix>__example_eligible_*.sql (strict user-defined matching, e.g.
#    "UC diagnosed 6-10 on first-line anti-TNF") and they are appended here.
#
# Generators are the source of truth. never hand-edit the generated
# athena/<prefix>__eligible_*.sql from the family. edit template/eligible_*.sql
# and regenerate. The example_eligible_* views ARE hand-authored (that is the
# guided layer).
#-----------------------------------------------------------------------------

# Rendered in dependency order (build:serial). each table reads the prior ones.
ELIGIBLE_FAMILY = [
    'eligible_dx',                 # best case/index (casedef match) date per subject
    'eligible_rx_date',            # treatment-class first-exposure dates + therapy lines
    'eligible_rx_date_evidence',   # normalized evidence refs per class
    'eligible_rx_date_prior_class',# prior classes before each line
    'eligible_outcome',            # first qualifying time-to-event outcome
    'eligible',                    # event-level eligibility + outcome risk set
    'eligible_timeline',           # analysis spine (time zero, exposure, TTE, baseline)
]

def make_eligible_family() -> list[Path]:
    """Render each generic template/eligible_*.sql into athena/<prefix>__eligible_*.sql."""
    return [template.copy(f"{name}.sql") for name in ELIGIBLE_FAMILY]

def list_study_eligible_views() -> list[Path]:
    """Pick up hand-authored study cohort-selection views (the guided layer)."""
    athena = filetool.path_athena()
    prefix = tablespace.name_prefix('')  # e.g. 'example__'
    family = {f"{prefix}{name}.sql" for name in ELIGIBLE_FAMILY}
    matches = sorted(athena.glob(f"{prefix}example_eligible_*.sql"))
    return [p for p in matches if p.name not in family]

def make() -> list[Path]:
    family = make_eligible_family()
    views = list_study_eligible_views()
    action = manifest.SqlAction(
        family + views,
        'computable phenotype + cohort views for eligible patients (TTE / CDS / matching)',
        'build:serial')
    return [manifest.save_actions_toml(action, 'eligible.toml')]

if __name__ == '__main__':
    for target in make():
        print(target)
