# eligible reference

Deep detail for the eligible stage: the generation chain, the best-date
resolution ladder, per-table column contracts, the analysis spine, leakage-safe
baseline covariate assembly, and a per-template adaptation checklist. Replace
`example` with your study prefix throughout.

## Generation chain

`tools/eligible.py`:

- `ELIGIBLE_FAMILY` lists the seven templates in dependency order.
- `make_eligible_family()` renders each `template/eligible_*.sql` (Jinja,
  `{{ prefix }}`) into `athena/<prefix>__eligible_*.sql` via `template.copy`.
- `list_study_eligible_views()` globs hand-authored
  `athena/<prefix>__example_eligible_*.sql` (the guided cohort views), excluding
  the family names.
- `make()` writes `eligible.toml` as one `build:serial` action = family + views.

Regenerate: `python -m cumulus_study_builder.tools.eligible` (or the whole
spine via `study_builder.py`), then `cumulus-library build`.

Upstream dependencies (built by earlier stages, safe to read):
`example__cohort_casedef` (case cohort with `casedef_period` pre/peri/post),
`example__cohort_timeline` (per-encounter spine with demographics + dates),
`example__cohort_variable_union` (long-form coded evidence with
`enc_period_start_day`), `example__cohort_variable_wide_<aspect>` (per-variable
dated/valued columns), and optionally `example__llm_timeline` / `example__llm_*_wide`
(chart-review outputs) when the chart-review stage runs.

## The best-date resolution ladder (`eligible_dx`)

`casedef_date_best` is the anchor. The pattern is a **priority ladder**: collect a
candidate date from each evidence source, then take the first non-null by priority
(`COALESCE(strongest, ..., weakest)`), tie-broken deterministically.

The shipped template uses one FHIR rung — the first case-defining encounter
(`casedef_period = 'peri'`) restricted to the strongest `tier`, earliest date,
then subtype specificity. To add rungs, model on the IBD ladder:

| Priority | Rung | Basis |
|---|---|---|
| 1 | LLM procedure/diagnosis date | strongest — a note explicitly stating establishment (join `example__llm_timeline`) |
| 2 | LLM general date | a note dating the case less specifically |
| 3 | FHIR `recordedDate` | structured record date on a tier-1 case-defining resource |
| 4 | FHIR linked-encounter date | the case-defining encounter start (the shipped rung) |
| 5 | FHIR onset date | last resort — symptom onset, off-concept |

Rules that generalize:

- Restrict FHIR rungs to **tier-1** case-defining evidence (`cohort_casedef.tier`).
- Same-date ties prefer the **more specific subtype** (in IBD: CD/UC > IBDU > IBD_NOS).
- Emit the winning value plus `_source`, `_source_priority`, and preserved per-rung
  columns so the choice is auditable.
- Add **disagreement diagnostics** for QA: signed day gap between the LLM and FHIR
  branch bests, a boolean when the gap exceeds a tolerance (IBD uses 90 days), and
  an extraction-instability span when an LLM extracts multiple dates for a subject.
- `has_casedef_date_best_bool` distinguishes eligible-but-not-dateable subjects.

To add the LLM rung: `UNION ALL` a candidate CTE that reads the LLM date from
`example__llm_timeline` (or an `example__llm_<task>_wide` table) with a lower
priority number, then let the ladder pick it. Guard it so the template still
renders when no LLM stage exists (the shipped template omits it for that reason).

## Therapy-line episode engine (`eligible_rx_date`)

Grain = subject × `rx_class` (× episode, once you add episodes). `rx_class` is an
rx-aspect study-variable name (author them with the study-variable skill; the
template matches `variable LIKE 'rx%'`).

Shipped template: `rx_sequence_date = MIN(event date)` per class, `DENSE_RANK` over
class first-dates = `rx_therapy_line_number`. To reach the full IBD engine, add:

- **Evidence source priority** (lower = stronger, drives which date anchors the
  line): 1 `MedicationDispense.whenHandedOver` (observed start), 2 LLM actual-start,
  3 `MedicationRequest.authoredOn` (decision), 4 request-linked encounter. Anchor =
  `MIN(COALESCE(actual_start, decision))`.
- **Episodes** (a class can recur): a same-class episode closes only on explicit
  failure evidence — LLM `PRIMARY_NON_RESPONSE` / `LOSS_OF_RESPONSE`, or a positive
  adverse event with status `STOPPED`. Elapsed time / missing refills do **not**
  close an episode. The next qualifying start opens the next episode = a later line.
- **Line-forming**: set `rx_is_line_forming = FALSE` for classes that are bridges or
  rescue (e.g. corticosteroids) so they stay as history but do not create a line.
- **Strategy labels**: class-level (`advanced_targeted`,
  `conventional_maintenance`, `steroid_bridge_or_rescue`) and line-level
  (combination, first-line active-comparator).

`eligible_rx_date_evidence` normalizes the supporting references (one row per
subject × class × resource_ref) so evidence is searchable/joinable rather than in
an array. `eligible_rx_date_prior_class` lists the distinct classes whose first
exposure precedes each line — the basis for step-up / top-down and prior-exposure
criteria.

## First outcome (`eligible_outcome`)

Grain = one row per subject in `eligible_dx` (outcome or not). Earliest qualifying
event wins; keep a deterministic source priority for same-date ties (IBD surgery:
`Procedure.performed` > LLM date > procedure-linked encounter > billing code =
upper bound). Default template selects procedure-aspect events
(`variable LIKE 'proc%'`) — repoint the `WHERE` at your outcome valueset (an
outcome study-variable, or a dx/proc subset). Columns: `outcome_has_qualifying`,
`outcome_date_first`, `outcome_type_first`, `outcome_source_first`,
`outcome_evidence_ref_first`.

## Risk set (`eligible`)

One row per therapy line, joined to the anchor date and (left) to the first
outcome. Key flags evaluated **at each line's anchor**:

- `outcome_free_at_anchor_bool` — no outcome, or outcome strictly after the anchor
  (same-day is **not** outcome-free, strict `>`).
- `is_outcome_risk_set_eligible_bool` = `rx_is_line_forming AND outcome_free_at_anchor_bool`.
- `days_anchor_to_outcome`, `outcome_on_anchor_date_bool`.
- `event_disposition` — mutually exclusive: `non_line_forming_treatment_history`,
  `outcome_at_or_before_anchor_history_only`, `eligible_outcome_risk_set`.

A line at or after the first outcome stays in the history but does not enter a
subsequent risk set.

## Analysis spine (`eligible_timeline`)

One row per line-forming episode. Fields fixed once, consistently across analyses:

- **Time zero / exposure**: `index_date` (= `rx_event_anchor_date`), `rx_class`,
  `rx_therapy_line_number`.
- **Anchor context**: `casedef_date_best`, `casedef_date_best_subtype` (provenance
  only), `days_casedef_to_index`. Add `age_at_casedef` / age-group for the study.
- **Demographics as of index**: from the closest `cohort_timeline` encounter on or
  before `index_date` (`age_at_visit`, `gender`, `race_display`,
  `ethnicity_display`, `demographics_encounter_ref`, `demographics_date`).
- **Outcome + censoring**: `outcome_event_bool` (outcome strictly after index),
  `outcome_event_observed` (0/1), `outcome_analysis_end_date` (outcome date when
  observed — even past the last encounter, since the event establishes observation —
  else `last_encounter_date`), `days_to_outcome_or_censor`, `last_encounter_date`,
  `outcome_risk_set_eligible_bool`.
- **Baseline observability**: `baseline_lookback_days` (365),
  `baseline_encounter_count`, `baseline_observation_start_date`,
  `baseline_observation_span_days`. `count = 0` means no observable baseline history.

Response / safety fields (if you carry them from the rx engine) describe evidence
assigned to the indexed episode and may be observed after index — **never use them
as baseline covariates**.

Censoring caveats: `last_encounter_date` is loss-to-follow-up (can be informative);
there is no death / competing-risk handling. Prefer a fixed administrative censor
as primary, and consider competing risks where mortality is non-trivial.

## Baseline covariates assembled externally (leakage-safe) — copy/paste

Covariates are **not** columns of the spine. Join the spine to the dated per-aspect
wide tables and window each variable by its own date strictly before `index_date`:

```sql
WITH spine AS (
    SELECT subject_ref, rx_class, rx_therapy_line_number, index_date
    FROM   example__eligible_timeline
    -- for a 1-row-per-patient matching set, add: WHERE <first-line single-strategy>
),
crp AS (
    SELECT s.subject_ref, s.rx_class, s.rx_therapy_line_number,
           lab.lab_crp_value, lab.lab_crp_unit, lab.lab_crp_date,
           ROW_NUMBER() OVER (
               PARTITION BY s.subject_ref, s.rx_class, s.rx_therapy_line_number
               ORDER BY lab.lab_crp_date DESC
           ) AS rn
    FROM   spine AS s
    JOIN   example__cohort_variable_wide_lab AS lab
      ON   lab.subject_ref = s.subject_ref
     AND   lab.lab_crp_value IS NOT NULL
     AND   lab.lab_crp_date <  s.index_date                          -- no leakage
     AND   lab.lab_crp_date >= DATE_ADD('day', -365, s.index_date)   -- bounded lookback
)
SELECT subject_ref, rx_class, rx_therapy_line_number,
       lab_crp_value AS baseline_crp_value, lab_crp_unit AS baseline_crp_unit
FROM   crp WHERE rn = 1;
```

Swap `lab_crp_*` for any `lab_<var>_*`, or another aspect table + date column
(`dx_<var>_onset`, `rx_<var>_date`, `proc_<var>_date`, `diag_<var>_date`). For a
uniform encounter-date anchor across all coded variables, use
`example__cohort_variable_union` (carries `enc_period_start_day` for every row, no
numeric values). Prespecify each covariate's window/date/aggregation in a
version-controlled script so definitions stay stable. This joined table — spine +
covariates, one row per unit — is the SQL CTAS input handed to Python for PSM/IPTW.

## Per-template adaptation checklist

| Template | Typical study edit |
|---|---|
| `eligible_dx` | Add an LLM rung above the FHIR rung if chart-review runs. adjust the tier / subtype tie-break to your casedef. for a procedure-defined study the "peri" encounter already IS the procedure date. |
| `eligible_rx_date` | Point at your rx-class study-variables. add the evidence-source priority and failure-driven episode engine. set `rx_is_line_forming = FALSE` for bridge/rescue classes. |
| `eligible_rx_date_evidence` | Usually unchanged. extend if you add non-union evidence (dispense, LLM). |
| `eligible_rx_date_prior_class` | Usually unchanged. it derives from `eligible_rx_date`. |
| `eligible_outcome` | Repoint `WHERE` at your outcome valueset. add source priority for same-date ties. |
| `eligible` | Adjust the risk-set predicate and `event_disposition` to your outcome and comparator design. |
| `eligible_timeline` | Add study demographics (age at casedef), and any prespecified named outcome fields. keep covariates external. |

## Worked guided cohort view (copy-paste)

The guided layer is hand-authored raw SQL (not a jinja template). `tools/eligible.py`
globs `athena/<prefix>__example_eligible_*.sql` and wires whatever it finds into
`eligible.toml` on the next regenerate, in dependency order after the generated family
it reads. A `.gitignore` exception keeps these one committable, so they travel with a
fork. **The filename and the table names carry your literal study prefix** — when you
set your prefix, name the file `<prefix>__example_eligible_<criteria>.sql` and use that
same prefix in the `CREATE VIEW` / `FROM` (replace `example` below with your prefix).

A clean, disease-agnostic starting point — the one-row-per-patient, first-line,
single-strategy set for PSM / IPTW (`rx_class` is the exposure; the outcome is the
generic time-to-event from `eligible_outcome`):

```sql
-- athena/example__example_eligible_firstline_single_agent.sql
CREATE OR REPLACE VIEW example__example_eligible_firstline_single_agent AS
WITH ranked AS (
    SELECT  t.subject_ref, t.rx_class, t.index_date,
            t.age_at_visit, t.gender,
            t.outcome_event_bool, t.days_to_outcome_or_censor,
            t.baseline_encounter_count,
            ROW_NUMBER() OVER (                        -- one row per patient
                PARTITION BY t.subject_ref
                ORDER BY t.index_date ASC, t.rx_class ASC) AS rn
    FROM    example__eligible_timeline AS t
    WHERE   t.rx_therapy_line_number = 1               -- first line only
      AND   t.outcome_risk_set_eligible_bool           -- in the outcome risk set
      AND   t.baseline_encounter_count >= 1            -- minimally observed pre-index
)
SELECT * FROM ranked WHERE rn = 1;
```

Edit the `WHERE` to your inclusion/exclusion criteria (age at casedef, subtype arm,
first-line failure, a qualifying outcome, top-down vs step-up), then
`python -m cumulus_study_builder.tools.study_builder` to wire it. Broader sets (all
lines, multiple classes per patient) need cluster-robust handling downstream.

## Which skill owns what

The `eligible` skill owns `template/eligible_*.sql`, `tools/eligible.py`,
`eligible.toml`, and the guided `example_eligible_*` cohort views. It reads the
outputs of study-encounter, study-variable, case-definition, and chart-review — so
build those first (see the study-builder spine skill).
