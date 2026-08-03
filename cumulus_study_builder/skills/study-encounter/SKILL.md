---
name: study-encounter
description: >-
  Configure and regenerate the study_encounter stage of a cumulus-study-builder
  study: the encounter selection filtered by study period, demographics, and
  encounter utilization. Use to change study dates or history inclusion, age or age
  groups, included genders, utilization thresholds, or to rebuild
  study_encounter.toml. The base encounter table has exactly one row per encounter_ref;
  multivalued encounter class, service, type, priority, reason, and discharge coding
  lives in encounter_enc. Edit include_* CSVs or templates and regenerate;
  never hand-edit generated Athena SQL.
---

# study-encounter — foundational encounter selection

`tools/study_encounter.py` renders `template/encounter*.sql`
(`{{ prefix }}`) into Athena and writes `study_encounter.toml`. The encounter selection
is defined by the `spreadsheet/include_*` CSVs uploaded through
`file_upload_encounter.toml`. Regenerate:

```bash
python -m cumulus_study_builder.tools.study_encounter
```

Never hand-edit `athena/*encounter*.sql`. Edit the CSVs for criteria or
the templates for structure.

The stage is named `study_encounter`, but its public Athena namespace is deliberately
short: `<prefix>__encounter` and `<prefix>__encounter_<aspect>`. Reserve
`<prefix>__cohort_<variable>` for valueset-defined variable cohorts.

## Grain contract

- `encounter`: exactly one row per non-null `encounter_ref`. It contains
  encounter identity, subject, dates and ordinal, status, and patient demographics.
- `encounter_enc`: zero or more rows per retained `encounter_ref`. It
  contains potentially multivalued class, service type, encounter type, priority,
  reason, discharge disposition, and calendar rollups.
- Other `encounter_<aspect>` tables contain linked FHIR evidence and may
  have multiple rows per encounter.

Do not move a multivalued coding column back into the base table. Join `_enc` only
when a downstream task explicitly needs encounter coding and can accept its grain.

## Knobs

| File | Columns | Controls |
|---|---|---|
| include_study_period.csv | period_start, period_end, include_history | Encounter years. Blank end means today; blank start means 2000-01-01. |
| include_age_at_visit.csv | age_min, age_max | Age-at-encounter bounds. |
| age_group.csv | age_at_visit, age_group, age_group_display | Integer age to analysis band. Every included age needs a row. |
| include_gender.csv | system, code, display | Included FHIR genders. |
| include_utilization.csv | enc_min, enc_max, days_min, days_max | Per-subject encounter-period count and duration thresholds. |
| include_diag_category.csv | system, code, display | DiagnosticReport category valueset. |

Confirm the requested criteria before editing because this stage scopes every
downstream variable, case definition, sample, and eligible table.
