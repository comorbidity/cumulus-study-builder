---
name: study-builder
description: >-
  Orchestration spine for building a Cumulus Library study from the cumulus-study-builder
  starter (or a cumulus-study-start fork). Drives the new-study intake and connects the
  stage and companion skills into one workflow: study-encounter, study-variable (with the
  rxnorm and loinc valueset companions), case-definition, chart-review and rapid-elastic
  for clinical-note evidence, and eligible. tools/study_builder.py regenerates every
  stage's submanifest TOML and rendered athena SQL in one pass. Use whenever someone
  wants to start, build, scaffold, or plan a whole study, understand the pipeline and
  stage dependencies, pick the next stage or skill, or regenerate the manifests. On
  start, FIRST set the study prefix, then elicit the study OBJECTIVE and design, then
  offer the two paths — "I'm feeling lucky" or "clarifying questions". Generators are the
  source of truth — never hand-edit the generated tomls or athena SQL; edit the inputs
  and regenerate.
---

# study-builder — the study spine

This is the **spine** that runs the new-study intake and connects the per-stage and
companion skills into one coherent build. It sequences the work, explains dependencies,
delegates each stage to the right skill, and drives the top-level regenerate.

`tools/study_builder.py` (`make_study()`) regenerates every stage's submanifest TOML
and rendered athena SQL in one pass, from the repo root:

```bash
python -m cumulus_library_<study>.tools.study_builder   # or: cumulus-study-builder build
```

`manifest.toml` wires the stages, in order, for `cumulus-library build`.

## The skills

The nine skills ship inside the installed `cumulus-study-builder` package
(`cumulus_study_builder/skills/`) and are synced into each study's agent directories
(`.claude/skills`, `.agents/skills`, `.codex/skills`, `.gemini/skills`) by
`cumulus-study-builder sync-skills`. A `cumulus-study-start` fork already has them
committed. Edit skills only in the builder package, then re-sync — never edit the synced
copies (they carry a `.synced-from-cumulus-study-builder` marker and are overwritten).

| Skill | Role in the build |
|---|---|
| **study-builder** | This spine. runs intake, sequences, regenerates; delegates authoring. |
| **study-encounter** | Encounter filtering by study period, demographics, and utilization. |
| **study-variable** | Coded valueset CSVs per FHIR aspect (dx, rx, lab, proc, diag). |
| **rxnorm** | Companion to study-variable. medication (`rx_`) valuesets via RxNorm / RxClass. |
| **loinc** | Companion to study-variable. lab / DiagnosticReport (`lab_`, `diag_`) valuesets via LOINC. |
| **case-definition** | The case + subtype valueset (`casedef.csv`) and the case cohort. |
| **chart-review** | Clinical-note evidence via LLM extraction (Pydantic models). |
| **rapid-elastic** | Clinical-note evidence via Elasticsearch retrieval (query topics, KQL). |
| **eligible** | Phenotype + analysis spine (index date, therapy lines, outcome, KM/Cox/PSM) for TTE, CDS, and matching. |

## Starting a new study — intake (do this in order)

When a researcher starts a study (e.g. from a fresh `cumulus-study-start` fork), walk
this intake before authoring anything. Capture the answers; they steer every downstream
skill.

1. **Set the study prefix.** Tables are named `<study_prefix>__<table>`. Ask for the
   prefix and set `study_prefix` in the study package's `manifest.toml` (the single
   source of truth — `tablespace.py` reads it from there). Rename the package directory
   and `pyproject.toml` name to match (`cumulus_library_<prefix>` /
   `cumulus-library-<prefix>`) if it still carries the `mystudy` placeholder.

2. **Elicit the OBJECTIVE.** Ask for a few-sentence, manuscript-style description of the
   study objective — the kind of summary you would read in a PubMed abstract. Keep it on
   file; the case-definition, variable, and eligible skills all reason from it.

3. **Ask the design intent.** Is the study primarily for **TTE** (target trial
   emulation), **CDS** (clinical decision support), **both**, or **something else**? This
   sets how the eligible stage frames index date, exposure, and outcomes.

4. **Ask for the substance.** Elicit, in narrative form: the **study variables of
   interest**, a **narrative description of the case definition**, and the **outcomes of
   interest**. These map onto study-variable, case-definition, and eligible respectively.

5. **Offer the two paths** and ask the researcher to choose:
   - **"I'm feeling lucky"** — proceed WITHOUT further clarifying questions.
   - **"clarifying questions"** — proceed with the guided, confirm-each-step flow.

## Path: "I'm feeling lucky"

Run the study-builder end to end with NO further prompting. Use the OBJECTIVE, design,
variables, case definition, and outcomes captured in intake to make best-effort choices,
delegating silently to each sub-skill:

- Draft the study-variable valuesets (rxnorm for medications, loinc for labs/diag).
- Draft `casedef.csv`.
- (Optionally) draft chart-review models and/or rapid-elastic query topics if the
  narrative clearly needs clinical-note evidence.
- Regenerate everything and produce the structured FHIR Athena SQL (below).

Everything produced this way is a **candidate a human must verify** — say so, and point
the researcher at the specific CSVs / models to review.

## Path: "clarifying questions" (guided)

Guide the researcher stage by stage, confirming each before advancing and running the
matching generator as soon as a stage's inputs are accepted:

1. **Study variables** — guide with **study-variable**.
   - Medication variables: study-variable **with the rxnorm** skill.
   - Laboratory variables: study-variable **with the loinc** skill.
   - When the coded variable definitions are **accepted by the researcher**, run:
     ```bash
     python -m cumulus_library_<study>.tools.study_variable
     python -m cumulus_library_<study>.tools.study_variable_wide
     ```

2. **Case definition** — guide with **case-definition**.
   - When the case definition is **accepted by the researcher**, run:
     ```bash
     python -m cumulus_library_<study>.tools.casedef
     python -m cumulus_library_<study>.tools.sample
     ```

3. **(Optional) chart review** — guide with **chart-review**.
   - When the chart-review Pydantic classes are **accepted by the researcher**, proceed.

4. **(Optional) rapid-elastic** — guide with **rapid-elastic**.
   - When the Elastic query definitions are **accepted by the researcher**, proceed.

5. **Regenerate and produce the structured FHIR artifacts.** Run the study's
   `study_builder.py` to regenerate every stage's submanifest TOML and Athena SQL:
   ```bash
   python -m cumulus_library_<study>.tools.study_builder   # or: cumulus-study-builder build
   ```

## Scope at study start — structured artifacts only

When a researcher is **starting** a new study, do NOT run the LLM extraction over the
`sample` notes. Producing a good note sample is more selective work (choosing which
notes to send to an LLM against a potentially large `sample_casedef*` table) and is
**out of scope here**. At this stage:

- Only produce the **structured FHIR data artifacts** — i.e. the Athena SQL for
  encounters, variables, the case definition, the sample-table definitions, and (if
  relevant) eligible.
- The chart-review and rapid-elastic skills author the *definitions* (Pydantic models,
  query topics); they do not run inference now.

## Guide the manual build

After the generators have produced the Athena SQL, **guide the researcher to run the
`cumulus-library` build commands manually** — do not assume a warehouse is configured.
Point them at their study prefix, for example:

```bash
cumulus-library build --target <study_prefix> --database <db> --workgroup <wg> ...
```

and let them supply the database / workgroup / profile for their environment.

## Jump to a stage

If the researcher names a task, skip intake and route:

- "study period / age / encounter utilization / which encounters" → `study-encounter`
- "add/edit a coded variable / valueset / codes" → `study-variable`
- "medication / drug class / rx valueset" → `rxnorm`
- "lab / analyte / LOINC / DiagnosticReport valueset" → `loinc`
- "case definition / who's a case / subtype" → `case-definition`
- "extract from notes / LLM / Pydantic model" → `chart-review`
- "search notes / Elastic / query topics / KQL" → `rapid-elastic`
- "eligibility / index date / therapy lines / outcome / survival / matching / cohort" → `eligible`

## Pipeline (stage → skill → generator → depends on)

| # | Stage | Skill(s) | Generator | Depends on |
|---|---|---|---|---|
| 1 | Study encounter | study-encounter | study_encounter.py | core FHIR |
| 2 | Study variables | study-variable (+ **rxnorm** rx, **loinc** lab/diag) | study_variable.py | 1 |
| 3 | Variable union / wide | study-variable | study_variable_wide.py | 2 |
| 4 | Case definition | case-definition | casedef.py | 1, 2 |
| 5 | Sample notes | (sample.py) | sample.py | 1, 4 |
| 6 | Note extraction (defs only at start) | chart-review (LLM) and/or rapid-elastic | llm/create_*.py / elastic | 5 |
| 7 | Eligible (phenotype + spine) | eligible | eligible.py | 2, 4, 6 |

Dependencies are why order matters: case-definition scans the study-encounter aspects
and joins the casedef valueset; eligible reads casedef, the variable-wide tables, and
the note-extraction outputs. Build earlier stages first.

The stage name remains `study_encounter`; its Athena tables use the shorter
`<prefix>__encounter*` namespace. Valueset-selected variable tables retain the distinct
`<prefix>__cohort_<variable>` namespace. **The case definition is required by default**
— the casedef / sample / eligible stages read `spreadsheet/casedef.csv`. A study that
defines its cases with its own SQL instead drops those stages from its
`tools/study_builder.py` (an explicit opt-out in the study-owned master build file).

## Rules

Generators own the `*.toml` and generated `athena/*.sql`. Never hand-edit them — edit
inputs (CSVs, `casedef.csv`, Pydantic models, `template/*.sql`) and regenerate. The
eligible family renders from `template/eligible_*.sql`; the one hand-authored SQL layer
is the eligible cohort views (`<prefix>__example_eligible_*`), committed in `athena/`
WITHOUT a `<prefix>__` filename prefix (hand-authored study SQL needs no template).
Respect dependency order when building or rebuilding. Delegate authoring to the
sub-skills; this spine coordinates and regenerates, it does not duplicate their logic.
