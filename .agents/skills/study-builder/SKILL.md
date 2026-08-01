---
name: study-builder
description: >-
  Orchestration spine for building a Cumulus Library study from the cumulus-study-builder
  starter. Connects the stage and companion skills into one workflow: study-population,
  study-variable (with the rxnorm and loinc valueset companions), case-definition,
  chart-review and rapid-elastic for clinical-note evidence, and eligible.
  tools/study_builder.py regenerates every stage's submanifest TOML and rendered athena
  SQL in one pass. Use whenever someone wants to build, scaffold, or plan a whole study,
  understand the pipeline and stage dependencies, pick the next stage or skill, or
  regenerate the manifests. On start, ask whether they want the full guided build
  (population, variables, case definition, note extraction, eligible) or to jump to a
  specific stage. Generators are the source of truth — never hand-edit the generated
  tomls or athena SQL; edit the inputs and regenerate.
---

# study-builder — the study spine

This is the **spine** that connects the per-stage and companion skills into one
coherent study build. It sequences the work, explains dependencies, delegates each
stage to the right skill, and drives the top-level regenerate. Replace `example` with
your study prefix.

`tools/study_builder.py` (`make_study()`) regenerates every stage's submanifest TOML
and rendered athena SQL in one pass:

```bash
python -m cumulus_study_builder.tools.study_builder
```

`manifest.toml` wires the stages, in order, for `cumulus-library build`.

## The skills (all of `.agents/skills/`)

| Skill | Role in the build |
|---|---|
| **study-builder** | This spine. sequences and regenerates; delegates authoring. |
| **study-population** | Stage 1. the base cohort (study period, age, gender, encounter utilization). |
| **study-variable** | Stage 2. coded valueset CSVs per FHIR aspect (dx, rx, lab, proc, diag). |
| **rxnorm** | Companion to study-variable. medication (`rx_`) valuesets via RxNorm / RxClass. |
| **loinc** | Companion to study-variable. lab / DiagnosticReport (`lab_`, `diag_`) valuesets via LOINC. |
| **case-definition** | Stage 4. the case + subtype valueset (`casedef.csv`) and the case cohort. |
| **chart-review** | Clinical-note evidence via LLM extraction (Pydantic models). |
| **rapid-elastic** | Clinical-note evidence via Elasticsearch retrieval (query topics, KQL). |
| **eligible** | Stage 7. phenotype + analysis spine (index date, therapy lines, outcome, KM/Cox/PSM) for TTE, CDS, and matching. |

Edit skills in `.agents/skills/`. each agent's own dir (`.claude/skills`,
`.codex/skills`, `.gemini/skills`) is a symlink to it.

## Ask the entry mode

On invocation, ask which the researcher wants (offer both):

- **Full guided build** — walk the pipeline in order, delegating each stage to its
  skill, confirming a stage is complete before advancing, then regenerate.
- **Jump to a stage** — they already know their stage (e.g. "add a lab variable", "fix
  the case definition"); route straight to that skill.

## Pipeline (stage → skill → generator → depends on)

| # | Stage | Skill(s) | Generator | Depends on |
|---|---|---|---|---|
| 1 | Study population | study-population | study_population.py | core FHIR |
| 2 | Study variables | study-variable (+ **rxnorm** rx, **loinc** lab/diag) | study_variable.py | 1 |
| 3 | Variable union / wide | study-variable | study_variable_wide.py | 2 |
| 4 | Case definition | case-definition | casedef.py | 1, 2 |
| 5 | Sample notes | (sample.py) | sample.py | 1, 4 |
| 6 | Note extraction | chart-review (LLM) and/or rapid-elastic (Elastic) | llm/create_*.py / elastic | 5 |
| 7 | Eligible (phenotype + spine) | eligible | eligible.py | 2, 4, 6 |

Dependencies are why order matters: case-definition scans the study-population aspects
and joins the casedef valueset; eligible reads casedef, the variable-wide tables, and
the note-extraction outputs. Build earlier stages first.

## Guided build

Walk the researcher through the stages in order, delegating to each skill:

1. **Population** — invoke `study-population`: set study period / age / gender /
   utilization. the base cohort everything filters from.
2. **Variables** — invoke `study-variable` for each coded valueset. For medications
   delegate to **rxnorm** (class-first RxNorm/RxClass `rx_` valuesets); for labs and
   DiagnosticReports delegate to **loinc** (`lab_` / `diag_` valuesets). Each becomes a
   cohort and flows into the union / wide tables.
3. **Case definition** — invoke `case-definition`: author `casedef.csv` (subtype +
   tier) that defines who is a case and their subtype/arm.
4. **(Optional) wide / union / timeline** — regenerated automatically from the variable
   and casedef lists; call it out so the researcher knows the tabular tables exist.
5. **Note extraction (optional)** — if the phenotype needs clinical text, pick the
   path: **chart-review** (LLM Pydantic models → JSON schema → NLP) for structured
   extraction, and/or **rapid-elastic** (query topics, KQL) for note retrieval. Both
   run over the sampled notes.
6. **Eligible** — invoke `eligible`: render the phenotype + analysis-spine family
   (best case/index date, therapy lines, outcome, risk set, KM/Cox/PSM timeline) and
   author the study cohort views.

Then regenerate all manifests (`study_builder.py`) and run `cumulus-library build`.

## Jump to a stage

If the researcher names a task, skip the wizard and route:

- "study period / age / who's included" → `study-population`
- "add/edit a coded variable / valueset / codes" → `study-variable`
- "medication / drug class / rx valueset" → `rxnorm`
- "lab / analyte / LOINC / DiagnosticReport valueset" → `loinc`
- "case definition / who's a case / subtype" → `case-definition`
- "extract from notes / LLM / Pydantic model" → `chart-review`
- "search notes / Elastic / query topics / KQL" → `rapid-elastic`
- "eligibility / index date / therapy lines / outcome / survival / matching / cohort" → `eligible`

## Set the prefix first

Tables are `<study_prefix>__<table>`. Set `study_prefix` in `manifest.toml` AND
`PREFIX` in `tools/tablespace.py` (keep identical; placeholder ships as `example`).

## Rules

Generators own the `*.toml` and generated `athena/*.sql`. Never hand-edit them — edit
inputs (CSVs, `casedef.csv`, Pydantic models, `template/*.sql`) and regenerate. The
eligible family renders from `template/eligible_*.sql`; the one hand-authored SQL layer
is the eligible cohort views (`example_eligible_*`). Respect dependency order when
building or rebuilding. Delegate authoring to the sub-skills; this spine coordinates
and regenerates, it does not duplicate their logic.
