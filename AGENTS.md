# AGENTS.md

Cross-agent guide for the **cumulus-study-builder** repository. Any coding
agent — Claude, OpenAI Codex / ChatGPT, Gemini — and any new contributor should start
here.

## What this repo is

A generic, installable **study-builder** for Cumulus Library FHIR studies. Python
generators render Jinja SQL templates into Athena tables from CSV and Pydantic inputs.
Fork it to own a new study. See `README.md` and `PACKAGING.md`.

## Skills live in `.agents/skills/` (single source of truth)

The reusable how-to skills are the real files under **`.agents/skills/`**. Each agent's
own directory is a relative symlink to that one folder, so there is no duplication and
no drift:

```
.agents/skills/            <- real files. edit here.
.claude/skills  -> ../.agents/skills
.codex/skills   -> ../.agents/skills
.gemini/skills  -> ../.agents/skills
```

Each skill is a `SKILL.md` (YAML frontmatter `name` + `description`, then a markdown
body), optionally with a `references/` folder. This is the Agent Skills open format,
read the same way across agents. Edit skills in `.agents/skills/`, never through an
agent's symlink.

## Start with the study-builder skill

Building or extending a study? Read `.agents/skills/study-builder/SKILL.md` first — it
is the spine that sequences the stage skills in dependency order:

| Skill | What it does |
|---|---|
| **study-population** | The base cohort: age, gender, study period, encounter utilization. |
| **study-variable** | Coded valueset CSVs per FHIR aspect (dx, rx, lab, proc, diag). |
| **rxnorm** | Companion to study-variable for medication (`rx_`) valuesets (RxNorm / RxClass). |
| **loinc** | Companion to study-variable for lab / DiagnosticReport (`lab_`, `diag_`) valuesets (LOINC). |
| **case-definition** | The case + subtype valueset (`casedef.csv`) and the longitudinal case cohort. |
| **chart-review** | Pydantic models for the LLM/NLP clinical-note extraction layer. |
| **rapid-elastic** | Elasticsearch clinical-note retrieval (query topics, KQL) — the search path to notes. |
| **eligible** | Phenotype + analysis spine (index date, therapy lines, outcome, KM/Cox/PSM timeline) for TTE, CDS, and patient matching. |

## Rules for agents

- **Generators are the source of truth.** Never hand-edit generated `*.toml` or
  `athena/*.sql`. Edit the inputs (CSVs, `casedef.csv`, Pydantic models,
  `template/*.sql`) and regenerate:
  `python -m cumulus_study_builder.tools.study_builder`.
- Terminology / valueset skills (study-variable, rxnorm, loinc) **write SQL but do not
  execute it**, and their proposed codes are candidates a human must verify.
- Prose comments use periods, not semicolons (house style).

## More

`README.md` (quickstart, stages) and `PACKAGING.md` (module + fork-and-own model).
