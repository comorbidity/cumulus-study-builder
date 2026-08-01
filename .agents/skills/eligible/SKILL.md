---
name: eligible
description: >-
  Build the eligible stage of a cumulus-study-builder study — the
  computable-phenotype and analytic layer for target trial emulation (TTE),
  clinical decision support (CDS), and patient matching. It renders a generic
  template family (best case/index date, therapy lines, a time-to-event outcome, a
  risk set, and a survival analysis spine) into CTAS tables for downstream
  Python/pandas, and guides study-specific cohort views. Use whenever someone wants
  to define eligibility, resolve the best casedef match date (diagnosis date, or a
  procedure date like kidney transplant), sequence treatment lines, define a
  time-to-event outcome, build a survival/KM/Cox/PSM analysis spine with
  leakage-safe baseline covariates, or author strict patient-matching cohort views.
  tools/eligible.py renders template/eligible_*.sql, so never hand-edit the
  generated SQL — edit the templates and regenerate. Probabilistic matching
  (PSM/IPTW) runs downstream in Python; this stage produces the tabular inputs.
---

# eligible — computable phenotype + analytic spine

The `eligible` stage turns the built study (population, variables, case
definition, optional chart-review) into the tables an analyst actually runs a
study on: an index/anchor date per subject, treatment lines, a time-to-event
outcome, risk-set eligibility, and a survival/matching **analysis spine**. Its
purpose is **target trial emulation (TTE)**, **clinical decision support (CDS)**,
and **patient matching**. Replace `example` below with your study prefix.

It has **two parts** (the "templates + guided" model):

1. A **generic template family** — `template/eligible_*.sql` rendered by
   `tools/eligible.py` into `athena/<prefix>__eligible_*.sql`. These are the
   reusable CTAS tables. the SQL inputs for downstream Python/pandas.
2. **Study-authored cohort views** — hand-written
   `athena/<prefix>__example_eligible_*.sql` (strict, user-defined matching) that
   `eligible.py` appends to the stage. This is the guided layer.

```bash
python -m cumulus_study_builder.tools.eligible   # render family + wire eligible.toml
```

Generators are the source of truth. never hand-edit the rendered
`athena/<prefix>__eligible_*.sql` from the family. edit `template/eligible_*.sql`
and regenerate. The `example_eligible_*` views ARE hand-authored (the guided layer).

## The family (stage order = data dependency)

| # | Table | Grain | What it establishes |
|---|---|---|---|
| 1 | `eligible_dx` | subject | **Best case/index (casedef match) date** via an evidence ladder. |
| 2 | `eligible_rx_date` | subject × class | Treatment-class first-exposure dates and **therapy lines**. |
| 3 | `eligible_rx_date_evidence` | subject × class × ref | Normalized evidence references (provenance). |
| 4 | `eligible_rx_date_prior_class` | subject × class | Distinct classes started **before** each line (step-up / top-down). |
| 5 | `eligible_outcome` | subject | First qualifying **time-to-event outcome** (date, type, source). |
| 6 | `eligible` | subject × class × line | Event-level eligibility + **outcome risk-set** flags at each anchor. |
| 7 | `eligible_timeline` | line-forming episode | **Analysis spine** for KM / Cox / PSM (time zero, exposure, TTE, baseline). |

## The best casedef match date (the ladder) — start here

The anchor of the whole stage is `eligible_dx.casedef_date_best`: the date the
case is *established*. This is study-specific and is the first thing to get right:

- **IBD** → the diagnosis-established date.
- **Kidney transplant** → the transplant **procedure** date.
- Generally → the date of the first case-defining evidence in
  `<prefix>__cohort_casedef` (the `casedef_period = 'peri'` encounter).

The template resolves it with an **evidence ladder** (strongest dated evidence
wins, ties broken by tier then earliest then subtype specificity). The shipped
template uses the FHIR case-defining encounter. If your study runs chart-review,
add a stronger **LLM rung** (e.g. an LLM-extracted diagnosis or procedure date
from `<prefix>__llm_timeline`) above the FHIR rung and let priority pick it — the
IBD study layers LLM endoscopy and general-diagnosis dates over the FHIR
`recordedDate` / linked-encounter / onset rungs. See the reference for the ladder
pattern. `casedef_date_best_subtype` is **provenance of the anchor only** — do not
use it for subtype arms.

## Time zero, exposure, outcome, censoring

`eligible_timeline` is the spine and fixes the things that must not vary across
analyses:

- **Time zero** = `index_date` (a therapy line's `rx_event_anchor_date`). one row
  per line-forming episode.
- **Exposure** = `rx_class` / `rx_therapy_line_number`.
- **Anchor context** = `casedef_date_best`, `days_casedef_to_index`.
- **Demographics as of index** = the closest encounter on or before `index_date`.
- **Outcome + censoring** = `outcome_event_bool`, `outcome_analysis_end_date`
  (outcome date if observed, else last encounter = loss-to-follow-up censor),
  `days_to_outcome_or_censor`. The outcome is strictly **after** time zero.
- **Baseline observability** = encounter count / earliest encounter in
  `[index − 365, index)`, so `FALSE`/absent covariates can be told apart from
  unobserved history.

Censoring caveat: last-encounter censoring can be informative, and there is no
competing-risk / death handling — consider a fixed administrative censor for a
real analysis. Say so when you hand this to an analyst.

## Baseline covariates are assembled EXTERNALLY (leakage-safe)

The spine deliberately does **not** materialize covariates — that would bake one
window and one aggregation into the table. Assemble them downstream by joining the
spine to the dated `<prefix>__cohort_variable_wide_<aspect>` tables (from the
study-variable stage), windowing each variable by its **own** date strictly before
`index_date`. This keeps numeric values (labs) and the window choice in the
analyst's hands and prevents look-ahead leakage. The reference has a copy-paste
"most-recent-before-index" covariate template.

## The two matching paths

- **Strict (user-defined criteria).** Author a
  `<prefix>__example_eligible_*.sql` cohort view that filters `eligible` /
  `eligible_timeline` by explicit criteria — age at diagnosis, subtype, first-line
  therapy failed, a qualifying outcome, top-down vs step-up. This is the same
  pattern the IBD `ibd-eligible` skill uses for named cohort views. Confirm each
  criterion before writing; ambiguous criteria get a clarifying question.
- **Probabilistic (PSM / IPTW).** This stage's job is only to emit the **SQL CTAS
  analytic table**: `eligible_timeline` joined to the externally-assembled
  baseline covariates, one row per unit, all covariates flattened. Propensity-score
  matching and IPTW weighting run **downstream in Python/pandas** (statsmodels /
  scikit-learn, lifelines for survival) off that exported table — not in SQL and
  not in this skill. Any study-variable covariate can enter the propensity model.
  For a clean one-row-per-patient matching set, use the first-line single-strategy
  subset (see the reference); broader sets need cluster-robust handling.

## Adapting the templates to your study

Each template is a generic scaffold keyed off the built study. The reference walks
each one, but the usual edits are: repoint `eligible_rx_date` at your rx-class
study-variables (names starting `rx`), repoint `eligible_outcome`'s `WHERE` at your
outcome valueset (default is procedure-aspect events, matching IBD surgery), add an
LLM rung to `eligible_dx` if you run chart-review, and refine `rx_is_line_forming`
(e.g. exclude bridging steroids). Edit `template/eligible_*.sql`, then regenerate.

## Rules

- `tools/eligible.py` renders the family and wires `eligible.toml`. never hand-edit
  the generated `athena/<prefix>__eligible_*.sql` or `eligible.toml`.
- The family is `build:serial` in dependency order. later tables read earlier ones.
- The `<prefix>__example_eligible_*` cohort views are the one hand-authored layer.
- Prose comments separate sentences with periods, not semicolons (house style).

See `references/eligible_reference.md` for the resolution ladder, the per-table
column contracts, the analysis-spine fields, the baseline-covariate SQL template,
and the per-template adaptation checklist.

## Worked examples

**Strict cohort.** "UC diagnosed 6–10 on a first-line advanced therapy that
failed." → author `athena/<prefix>__example_eligible_uc_firstline_fail.sql` as a
view over `eligible_timeline` filtered on subtype, age at diagnosis band,
`rx_therapy_line_number = 1`, strategy, and the line-failure flag. print the
regenerate command.

**Matching table.** "Give me a PSM-ready table for first-line advanced vs
conventional." → confirm the exposure contrast, select the first-line
single-strategy subset of `eligible_timeline`, join the leakage-safe baseline
covariates (reference template), and emit one CTAS table. hand it to Python for the
propensity model — this stage stops at the SQL.
