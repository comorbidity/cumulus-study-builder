# Packaging — module + fork-and-own study template

**Status: the module end-state described below HAS LANDED (v1.0.0).** The spine is
a pip-installable package with a CLI (`init`, `build`, `sync-skills`); the five
reference studies were migrated off their vendored copies with byte-identical
regenerated output (see `MIGRATION.md`). The rest of this document records the
original reasoning.

## Why (what the reference studies showed)

The `tools/` + `template/` generator design is already used by several studies —
`cumulus-library-ibd-cds` (`ibd`), `cumulus-library-kidney-transplant` (`irae`),
`cumulus-library-glioma`, `cumulus-library-cabot`. **Each one vendored its own copy
of the spine, and they have drifted:** kidney-transplant added `tools/drug_eras.py`,
`tools/vocab.py`, `tools/guard.py`, a `refactor/` package; glioma added
`tools/casedef_rx_variables.py`; cabot added `tools/schema.py` and a `vital` aspect.
The same `study_encounter.py` / `casedef.py` / `manifest.py` now exist in four
slightly-different versions. A bug fixed in one is not fixed in the others.

That drift is the maintenance problem a module solves: **fix the spine once, version
it, PR-review it centrally, and let studies pick it up by bumping a dependency.** It
also matches the wider Cumulus ecosystem, where `cumulus-library` is an installable
package (`pip install cumulus-library`, the `cumulus-library` CLI, `BaseTableBuilder`,
`StudyManifest`) and each study is a thin repo that depends on it and is registered in
`cumulus_library/module_allowlist.json` (where `ibd` is already listed).

## The boundary

| Layer | Belongs to | Files |
|---|---|---|
| **Spine (module)** — stable, versioned, PR-reviewed | `cumulus-study-builder` | `cumulus_study_builder/tools/*.py`, `cumulus_study_builder/template/*.sql`, `.agents/skills/*` |
| **Study inputs (fork-and-own)** — per study | your study repo | `spreadsheet/*.csv` (include_*, valuesets, `casedef.csv`), `llm/models/*.py`, `manifest.toml` (`study_prefix`), the `example_eligible_*` cohort views, study-specific `template` overrides |
| **Generated (never hand-edit)** — output | your study repo | `<prefix>__*.toml`, `athena/<prefix>__*.sql` |

The module depends on `cumulus-library`; a study depends on
`cumulus-study-builder`.

## Where this repo is today, and the one change to finish the split

Today this repo is BOTH the module and a worked `example` study in one tree — which is
exactly how `ibd`/`kidney`/`glioma`/`cabot` started (fork the whole thing, rename,
replace the study inputs). That is the **fork-and-own** path and it works now:

1. Fork this repo. rename `cumulus_study_builder/` → `cumulus_library_<name>/`
   and the `pyproject.toml` name to `cumulus-library-<name>`.
2. Set `study_prefix` in `manifest.toml` and `PREFIX` in `tools/tablespace.py`.
3. Replace the study inputs (spreadsheet CSVs, `casedef.csv`, `llm/models`, the
   eligible cohort views). keep `tools/` + `template/` + `.agents/skills/`.
4. `pip install -e .` → `python -m cumulus_library_<name>.tools.study_builder` →
   `cumulus-library build`.

**The change that made this a true installable module (landed in v1.0.0 as
`tools/studydir.py`):** `tools/filetool.py` currently resolves every path relative to
the installed package dir (`Path(__file__).parent.parent`). For a study to keep its
own inputs/outputs while importing the module, `filetool` must resolve the *study
root* from the working directory or a `CUMULUS_STUDY_DIR` env var (mirroring
`cumulus-library`'s `--study-dir` / `CUMULUS_LIBRARY_STUDY_DIR`). That is the single
seam between "forkable template" (today) and "pip-installed spine + thin study repo"
(end state). Everything else — the generators, templates, skills — is already
study-agnostic.

Recommended sequence: ship this as the forkable template now, then land the
`filetool` study-root change + publish `cumulus-study-builder` to PyPI, then
migrate the existing studies off their vendored spines onto the dependency.
