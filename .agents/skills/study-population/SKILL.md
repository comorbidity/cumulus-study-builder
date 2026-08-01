---
name: study-population
description: >-
  Configure and regenerate the study_population stage of a cumulus-study-builder
  study — the base cohort of patient encounters (demographics, encounter
  utilization, study period). Use to change the study-period date range or history
  flag, the age range or age-group bands, included genders, or the
  encounter-utilization thresholds; or to rebuild study_population.toml. The knobs
  are the include_* CSVs in spreadsheet/. study_population.py is the generator and
  the athena SQL is generated, so never hand-edit it. Confirm before changing the
  population, since it changes the whole study downstream.
---

# study-population — foundational cohort

`tools/study_population.py` renders `template/cohort_study_population*.sql`
(`{{ prefix }}`) into athena and writes `study_population.toml`. The population is
defined by the `spreadsheet/include_*` CSVs (uploaded via
`file_upload_population.toml`). Regenerate:

```bash
python -m cumulus_study_builder.tools.study_population
```

Never hand-edit `athena/*cohort_study_population*.sql` — edit the CSVs (content) or
`template/` (logic).

## Knobs (spreadsheet/)

| File | Columns | Controls |
|---|---|---|
| include_study_period.csv | period_start, period_end, include_history | Encounter years. Blank end → today; blank start → 2000-01-01. |
| include_age_at_visit.csv | age_min, age_max | Age-at-encounter bounds (starter default 0–120). |
| age_group.csv | age_at_visit, age_group, age_group_display | One row per integer age → a band + label. Every included age needs a row. |
| include_gender.csv | system, code, display | Included FHIR genders. |
| include_utilization.csv | enc_min, enc_max, days_min, days_max | Min/max distinct encounter periods and days between first/last encounter. |
| include_diag_category.csv | system, code, display | DiagnosticReport category valueset. |

Recipes: change the study period (edit include_study_period); change/narrow ages
(edit include_age_at_visit AND extend age_group to cover the range); tighten to a
longitudinal cohort (raise enc_min / days_min). Confirm exact values before editing.
