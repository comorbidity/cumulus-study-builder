# cumulus-study-builder

The shared, **versioned spine** for building
[Cumulus Library](https://docs.smarthealthit.org/cumulus/) studies over FHIR data:
Python generators that render Jinja SQL templates into Athena tables from a few CSV
inputs, plus a clinical-note extraction layer (LLM chart-review and Elastic
retrieval), a generic **eligible** analytic layer, and nine agent **skills** —
all installed as ONE pip package that every study depends on. Studies do NOT fork
this repo.

## Install & create a study (newcomers start here)

```bash
pip install "cumulus-study-builder @ git+https://github.com/smart-on-fhir/cumulus-study-builder.git@v1.0.0"
cumulus-study-builder init my-study --prefix mystudy
cd cumulus-library-my-study
pip install -e .
cumulus-study-builder build          # renders every athena/*.sql + submanifest TOML
cumulus-library build --target mystudy
```

`init` scaffolds a THIN study repo: starter spreadsheets, a `manifest.toml` with
your `study_prefix`, an empty `template/` for overrides, tests, and the agent
skills (synced into `.claude/`, `.agents/`, `.codex/`, `.gemini/`). Everything
else — generators, canonical SQL templates, skills — comes from the installed,
pinned builder.

## The distribution model

| Layer | Lives in | Changes via |
|---|---|---|
| **Spine** — `tools/*.py` generators, `template/*.sql`, `skills/` | this repo, installed via pip, pinned by tag | PR review here, then a tagged release |
| **Study inputs** — `spreadsheet/*.csv`, `manifest.toml`, `study_builder.toml`, template *overrides*, study-specific tools | each study repo | PRs in the study repo |
| **Generated** — `athena/<prefix>__*.sql`, submanifest `*.toml` | each study repo | never hand-edit; re-run `cumulus-study-builder build` |

Three mechanisms make the thin-study model work:

1. **Dynamic study root** (`tools/studydir.py`): every generator resolves the
   study package dir from `CUMULUS_STUDY_DIR` or the working directory — never
   from the installed package location.
2. **Study-first template resolution** (`tools/template.py`): a template in the
   study's own `template/` overrides the packaged one with the same filename;
   delete the override to fall back to the shared, PR-reviewed copy.
3. **Skill sync** (`cumulus-study-builder sync-skills`): packaged skills are
   copied into the study's agent dirs with a version marker; a skill dir
   WITHOUT the marker is yours and is never touched.

Per-study knobs (`data_package_version`, `cube_min_subjects`, `cube_as_view`,
`encounter_ref`) live in `study_builder.toml` next to the study's
`manifest.toml`; environment variables (`CUMULUS_*`) override.

## Updating a study to a new spine release

```bash
# in the study repo: bump the tag in pyproject.toml, then
pip install -e .
cumulus-study-builder build     # regenerate
git diff                        # review exactly what the new spine changes
cumulus-study-builder sync-skills
```

The regenerated SQL diff IS the review artifact: a spine bump lands in a study
as an ordinary PR whose diff shows precisely what changed in the study's tables.

This repo also remains a runnable worked `example` study (the packaged
`cumulus_study_builder/` dir doubles as one), so its own tests exercise the
whole pipeline. See `PACKAGING.md` for the history and rationale of this model
and `MIGRATION.md` for converting a pre-existing vendored study.

## The stages (the spine)

`tools/study_builder.py` regenerates every stage in dependency order:

| Stage | You edit | Generator |
|---|---|---|
| study_encounter | `spreadsheet/include_*.csv` (study period, age, gender, utilization) | `tools/study_encounter.py` |
| study_variable | `spreadsheet/<aspect>_<name>.csv` coded valuesets | `tools/study_variable.py` |
| study_variable_wide | (auto from the variable list) | `tools/study_variable_wide.py` |
| casedef | `spreadsheet/casedef.csv` (subtype, system, code, display, tier) | `tools/casedef.py` |
| sample | (auto — samples notes for chart review) | `tools/sample.py` |
| chart-review (LLM) | `llm/models/*.py` Pydantic models | `llm/create_*.py` |
| eligible | `template/eligible_*.sql` family (generated) + hand-authored `example_eligible_*` cohort views | `tools/eligible.py` |

The foundational `<prefix>__encounter` table has exactly one row per
non-null `encounter_ref`. It keeps encounter identity, subject, dates/ordinal, status,
and patient demographics. Potentially multivalued class, service type, encounter type,
priority, reason, and discharge-disposition coding lives in
`<prefix>__encounter_enc`, which may contain multiple rows per encounter.
The source family is `template/encounter*.sql`, rendered as
`athena/<prefix>__encounter*.sql`. Valueset-defined variables remain in the separate
`<prefix>__cohort_<variable>` namespace.

Aspects (FHIR resources): `enc, dx, rx, lab, proc, doc, diag, allergy`.

Valueset companions: **rxnorm** (medication `rx_` valuesets) and **loinc** (`lab_` /
`diag_` valuesets) assist study-variable; **rapid-elastic** is an Elasticsearch path to
clinical notes alongside **chart-review**. `spreadsheet/` ships an example valueset for
each aspect (`dx_example`, `rx_example`, `lab_example`, `diag_example`, `proc_example`).

## Set your study prefix

Tables are named `<study_prefix>__<table>`. Set it in **one** place:
`manifest.toml` → `study_prefix`. (`tools/tablespace.py` reads it from there;
the old two-places rule is gone.)

The starter ships with the placeholder `example`.

## Quickstart

```bash
# 1. install (editable; add the [test] extra so step 4's pytest is available)
pip install -e ".[test]"

# 2. regenerate every submanifest TOML + rendered athena SQL
python -m cumulus_study_builder.tools.study_builder

# 3. (chart review, optional) regenerate JSON schemas + summaries from models
python -m cumulus_study_builder.llm.create_schema
python -m cumulus_study_builder.llm.create_model_summary

# 4. (optional) run the template/render tests
pytest

# 5. build against your database (uses your study_prefix as the target)
cumulus-library build --target example
```

Steps 1–3 and the tests run **standalone** — no source study or database required —
and are verified (the full spine incl. the eligible family renders, the SQL parses as
Trino, `pytest` green). Step 5 needs your Athena/database connection.

## Rule of the road

The `*.toml` and generated `athena/*.sql` files are **generated** — never hand-edit
them. Edit the inputs (the `include_*` / valueset CSVs, `casedef.csv`, the Pydantic
models, or the `template/*.sql` sources) and regenerate. The `eligible` family
renders from `template/eligible_*.sql`. The one hand-authored SQL layer is the study
cohort views (`athena/<prefix>__example_eligible_*.sql`) — the sole committed exception
in `athena/` (a `.gitignore` rule keeps them tracked; everything else in `athena/` is
regenerated and ignored).

## Layout

```
cumulus_study_builder/
  manifest.toml            top-level stage wiring (set study_prefix here)
  tools/*.py               the generators (the spine)
  template/*.sql           Jinja SQL rendered into athena/
  athena/                  generated SQL (regenerated by the tools; git-ignored)
  llm/                     chart-review: models/ (Pydantic), create_*.py, template/
spreadsheet/               CSV inputs (include_*, valuesets, casedef.csv) + file_upload_*.toml
tests/                     template QA tests + test scaffolding
.agents/skills/            nine skills (single source): study-builder, study-encounter,
                           study-variable, rxnorm, loinc, case-definition, chart-review,
                           rapid-elastic, eligible
.claude/skills -> ../.agents/skills   (per-agent symlinks: .claude, .codex, .gemini)
AGENTS.md                  cross-agent entry point + skill index
```

See `AGENTS.md` for the cross-agent layout and skill index, and `PACKAGING.md` for the
module + fork-and-own model.
