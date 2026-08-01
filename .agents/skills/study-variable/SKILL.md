---
name: study-variable
description: >-
  Author CSV valuesets for FHIR-coded study variables in a
  cumulus-study-builder study. A variable is a spreadsheet CSV named
  aspect_name.csv (required system, code, display, plus optional per-code columns
  like tier, rank, subtype, or category) targeting a FHIR resource — dx=Condition,
  rx=MedicationRequest, lab=Observation lab, proc=Procedure, diag=DiagnosticReport —
  and each produces an example__cohort_ table sub-selected from study_population that
  flows into the UNION and wide per-aspect tables. Use whenever someone wants to
  create, edit, or add a coded study variable or valueset (labs, diagnoses,
  medications, procedures, diagnostic reports, symptoms), pick or expand codes, or
  rebuild the study_variable / study_variable_wide stage. Offer two modes:
  feeling-lucky or clarifying. Add optional columns only when a downstream decision
  reads them. The tomls and athena SQL are generated, so never hand-edit them —
  author the CSV and regenerate. Proposed codes are candidates a human must verify.
---

# study-variable — coded valueset authoring

Author **one CSV per variable**; everything else — the file-upload registration, the
per-variable cohort SQL, and the multi-variable UNION and wide tables — is generated.
Replace `example` below with your study prefix.

A variable targets one FHIR resource ("aspect"):

| Aspect | FHIR resource | study_population table | code / system columns |
|---|---|---|---|
| `dx` | Condition | `example__cohort_study_population_dx` | `dx_code` / `dx_system` |
| `rx` | MedicationRequest | `example__cohort_study_population_rx` | `rx_code` / `rx_system` |
| `lab` | Observation (category lab) | `example__cohort_study_population_lab` | `lab_observation_code` / `lab_observation_system` |
| `proc` | Procedure | `example__cohort_study_population_proc` | `proc_code` / `proc_system` |
| `diag` | DiagnosticReport | `example__cohort_study_population_diag` | `diag_code` / `diag_system` |

## How the stage generates (never hand-edit the SQL)

`tools/study_variable.py::make()`:
1. Writes `spreadsheet/file_upload_study_variable.toml` from the valueset CSVs
   (each `<aspect>_<name>.csv` → `example__valueset_<name>`).
2. Generates one `athena/example__cohort_<name>.sql` per variable — a
   `SELECT DISTINCT *` of `study_population_<aspect>` joined to `valueset_<name>` on
   **code + system** (extra CSV columns like `tier` flow through the `*`).
3. Writes `study_variable.toml` (the build list).

`tools/study_variable_wide.py::make()` then generates, from the same variable list:
- `example__cohort_variable_union` and `example__cohort_variable_union_<aspect>`
  (long form, one `variable`-labelled row per coded evidence hit), and
- `example__cohort_variable_wide` and `example__cohort_variable_wide_<aspect>`
  (pivoted, one column group per variable) — plus `study_variable_wide.toml`.

Both generators derive their variable list from the CSVs in `spreadsheet/`, so **a
new variable needs only a new CSV** — cohort, union, and wide tables all pick it up
on regenerate. Never hand-edit `athena/example__cohort_*` or the tomls; edit the CSV
(content) or the `template/` union/wide sources (structure).

## The valueset CSV

Name: `spreadsheet/<aspect>_<name>.csv`. The leading token is the aspect and must be
one of `dx`, `rx`, `lab`, `proc`, `diag` (it routes the code/system columns via
`fhir_reference`). Examples: `lab_ferritin.csv`, `dx_symptom_fatigue.csv`,
`proc_endoscopy.csv`, `diag_pathology.csv`.

**Required columns (all aspects):** `system`, `code`, `display`. One code per row.
The cohort join matches on `code` + `system` only, so those two must exactly match
how the codes appear in the `core__*` data; `display` is descriptive. Keep the
header consistent across every row.

**Optional columns:** additional per-code columns after the required three. They are
not matched on — they pass through the per-variable cohort via `SELECT DISTINCT *`
and become columns of `example__cohort_<name>`. Add them **only when the extra
metadata is needed for branching logic** (a downstream decision that reads the column
to take a different path). Keep valuesets lean; name optional columns lowercase and
put them on every row. Common ones: `tier` (evidence specificity: `1` =
high-specificity direct match, `3` = broader/adjacent), `rank` (priority when
several codes fire), `subtype` (a code that applies to one arm vs another),
`category` (a grouping a decision switches on). If no branch reads it, leave it out.

**Propagation caveat:** optional columns live in the individual
`example__cohort_<name>` table. They are **not** automatically carried into
`example__cohort_variable_union_*` or `example__cohort_variable_wide_*`, which
project a fixed set (`variable, code, display, system` plus the study_population
aspect columns). To use an optional column in the wide/union layer, join back to
`example__cohort_<name>` on `code` + `system`, or extend the `template/` union/wide
source to carry it.

Code systems by aspect (for choosing `system`):

- **dx:** ICD-10-CM `http://hl7.org/fhir/sid/icd-10-cm`, ICD-9-CM
  `http://hl7.org/fhir/sid/icd-9-cm`, SNOMED CT `http://snomed.info/sct`, local
  `urn:oid:...`.
- **rx:** RxNorm `http://www.nlm.nih.gov/research/umls/rxnorm`, plus NDC / local. For
  medication valuesets, use the **rxnorm** companion skill (class-first RxNorm /
  RxClass authoring) — it produces the `rx_class_*` CSV this stage registers.
- **lab / diag:** LOINC `http://loinc.org`, plus SNOMED and local `urn:oid:...`.
- **proc:** CPT `http://www.ama-assn.org/go/cpt`, HCPCS, ICD-10-PCS, SNOMED.

## Two authoring modes — ask which up front

**"I'm feeling lucky"** — generate a best-effort candidate valueset immediately:
infer the concept, pick the sensible code systems for the aspect, and populate a
reasonable set of codes with displays (and tiers for dx). Present for review. Fast;
the researcher scans and prunes.

**"Clarifying questions"** — elicit intent before writing. Ask the few questions that
actually change the code selection: exact concept boundary; which code systems to
include; breadth (specific codes only, or broader/related at a higher tier);
inclusions/exclusions (e.g. exclude "history of", unspecified); for rx,
ingredient-level or include combination products / brand names. Then generate.

In **both** modes, end with the same honest caveat: **the codes are candidates.**
Proposed codes must be verified against an authoritative source (VSAC value sets,
LOINC/RxNorm/SNOMED browsers, or the site's own terminology) and checked against the
actual `core__*` data, since a code that isn't present links nothing. Do not present
generated codes as validated.

## Regenerate (write CSV, then instruct — do not auto-run)

After writing the CSV, tell the researcher to run, from the repo root:

```bash
python -m cumulus_study_builder.tools.study_variable
python -m cumulus_study_builder.tools.study_variable_wide
```

The first regenerates `file_upload_study_variable.toml`, the per-variable cohort SQL,
and `study_variable.toml`; the second regenerates the union/wide SQL and
`study_variable_wide.toml`. A subsequent `cumulus-library build` (or the study
builder) materializes the new `example__valueset_<name>`, `example__cohort_<name>`,
and the refreshed union/wide tables. The new variable flows into the wide tables
automatically — no manual wiring.

## What downstream sees

`example__cohort_<name>` is the variable's cohort (population rows matching the
valueset). `example__cohort_variable_wide_<aspect>` exposes it as `<name>_date`,
`<name>_status`/`_onset`, `<name>_ref`, etc. — the join surface the eligible and
example layers use. A well-named, well-coded variable becomes immediately usable by
the eligible / cohort-view layer.

## Header comment style

The generated SQL has no comments to maintain. If you edit a `template/` union/wide
source, separate sentences in prose comments with periods, not semicolons (house
style); colons are fine for labels.

## Worked examples

**Feeling lucky.** "Add a lab variable for fecal calprotectin." → aspect `lab`, file
`spreadsheet/lab_calprotectin.csv`, header `system,code,display`, populate LOINC
calprotectin codes with displays, present for review, print the two regenerate
commands, note the codes need verification.

**Clarifying.** "Add a dx variable for arthralgia." → ask: symptom vs formal
diagnosis? ICD-10 only or SNOMED too? include unspecified? Then write
`spreadsheet/dx_symptom_arthralgia.csv` (`system,code,display,tier`) with tier-1
direct codes and tier-3 broader ones, present, print the regenerate commands.
