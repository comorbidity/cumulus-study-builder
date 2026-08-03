# Athena query patterns for LOINC valueset discovery

## Contents

- Safety contract
- Local LOINC schema
- Core term search
- Group search and expansion
- Lab-order search
- Selected-code validation
- Cumulus discovery queries
- Reconciliation
- SQL file set

## Safety contract

Use these patterns to create concrete `.sql` files. Replace semantic search terms and
environment placeholders before delivery. Never execute the files as part of the
`loinc` skill.

Generate read-only `SELECT`/CTE queries. Do not use CTAS, `CREATE`, `INSERT`,
`UPDATE`, `DELETE`, `DROP`, or `UNLOAD`. The Cumulus LOINC study reserves the
dedicated `loinc` schema; never create tables there.

Put this metadata in each SQL header:

```sql
-- Purpose:
-- Clinical concept/analyte:
-- Inclusion and exclusion assumptions:
-- Expected grain:
-- Source tables:
-- LOINC version: verify at execution time
-- Execution status: NOT EXECUTED by the loinc skill
```

## Local LOINC schema

The current `cumulus-library-loinc` builder loads these tables into the dedicated
`loinc` schema:

| Table | Important columns |
|---|---|
| `loinc.loinc_core` | `loinc_num`, `component`, `property`, `time_aspct`, `system`, `scale_typ`, `method_typ`, `class`, `classtype`, `long_common_name`, `shortname`, `status`, `version_first_released`, `version_last_changed` |
| `loinc.map_to` | `loinc`, `map_to`, `comment` |
| `loinc.parent_group` | `parent_group_id`, `parent_group`, `status` |
| `loinc.parent_group_attributes` | `parent_group_id`, `type`, `value` |
| `loinc."group"` | `parent_group_id`, `group_id`, `group`, `archetype`, `status`, `version_first_released` |
| `loinc.group_loinc_terms` | `category`, `group_id`, `archetype`, `loinc_number`, `long_common_name` |
| `loinc.group_attributes` | `parent_group_id`, `group_id`, `type`, `value` |
| `loinc.lab_orders` | `loinc_num`, `long_common_name`, `order_obs` |
| `loinc.document_ontology` | `loinc_number`, `part_number`, `part_type_name`, `part_sequence_order`, `part_name` |

The builder also loads `consumer_name`, primarily for consumer-friendly names. Do not
assume that the local schema includes the full LOINC distribution. In particular,
Panels-and-Forms is not currently loaded.

Quote `"group"` because `GROUP` is a SQL keyword. All builder columns are strings;
cast deliberately when numeric behavior is required.

## Core term search

Create a concrete term-search file such as `loinc_<slug>_core_search.sql`:

```sql
WITH search_terms(term) AS (
    VALUES
        ('<analyte term>'),
        ('<accepted synonym>')
)
SELECT DISTINCT
       search_terms.term AS matched_search_term,
       core.loinc_num,
       core.long_common_name,
       core.component,
       core.property,
       core.time_aspct,
       core.system,
       core.scale_typ,
       core.method_typ,
       core.class,
       core.status,
       core.version_first_released,
       core.version_last_changed
FROM loinc.loinc_core AS core
CROSS JOIN search_terms
WHERE core.status = 'ACTIVE'
  AND (
      LOWER(COALESCE(core.component, ''))
          LIKE CONCAT('%', LOWER(search_terms.term), '%')
      OR LOWER(COALESCE(core.long_common_name, ''))
          LIKE CONCAT('%', LOWER(search_terms.term), '%')
      OR LOWER(COALESCE(core.shortname, ''))
          LIKE CONCAT('%', LOWER(search_terms.term), '%')
  )
  -- Add explicit Property/System/Scale/Method inclusions and exclusions here.
ORDER BY core.component, core.system, core.property, core.method_typ, core.loinc_num
;
```

Do not stop at text matching. Add axis predicates derived from the researcher's
definition. Avoid a broad `LIKE '%iron%'` query when the question distinguishes
serum iron, ferritin, transferrin, binding capacity, and saturation.

## Group search and expansion

Search for relevant Groups first:

```sql
WITH search_terms(term) AS (
    VALUES ('<group/analyte term>')
)
SELECT DISTINCT
       search_terms.term AS matched_search_term,
       groups.parent_group_id,
       groups.group_id,
       groups."group" AS group_name,
       groups.archetype,
       groups.status,
       parent.parent_group,
       parent.status AS parent_group_status
FROM loinc."group" AS groups
LEFT JOIN loinc.parent_group AS parent
  ON parent.parent_group_id = groups.parent_group_id
CROSS JOIN search_terms
WHERE LOWER(COALESCE(groups."group", ''))
          LIKE CONCAT('%', LOWER(search_terms.term), '%')
   OR LOWER(COALESCE(parent.parent_group, ''))
          LIKE CONCAT('%', LOWER(search_terms.term), '%')
ORDER BY groups.parent_group_id, groups.group_id
;
```

Expand only reviewed Group IDs:

```sql
WITH selected_groups(group_id) AS (
    VALUES ('<reviewed LG identifier>')
)
SELECT DISTINCT
       members.category,
       members.group_id,
       groups."group" AS group_name,
       members.archetype,
       members.loinc_number,
       members.long_common_name,
       core.component,
       core.property,
       core.time_aspct,
       core.system,
       core.scale_typ,
       core.method_typ,
       core.status
FROM selected_groups
JOIN loinc.group_loinc_terms AS members
  ON members.group_id = selected_groups.group_id
LEFT JOIN loinc."group" AS groups
  ON groups.group_id = members.group_id
LEFT JOIN loinc.loinc_core AS core
  ON core.loinc_num = members.loinc_number
ORDER BY members.group_id, members.loinc_number
;
```

Review every member. Do not copy `group_id` into the study-variable CSV.

## Lab-order search

Use `lab_orders` to distinguish orderable codes from result-oriented candidates:

```sql
WITH search_terms(term) AS (
    VALUES ('<order or panel term>')
)
SELECT DISTINCT
       search_terms.term AS matched_search_term,
       orders.loinc_num,
       orders.long_common_name,
       orders.order_obs,
       core.status,
       core.component,
       core.system,
       core.scale_typ
FROM loinc.lab_orders AS orders
LEFT JOIN loinc.loinc_core AS core
  ON core.loinc_num = orders.loinc_num
CROSS JOIN search_terms
WHERE LOWER(COALESCE(orders.long_common_name, ''))
          LIKE CONCAT('%', LOWER(search_terms.term), '%')
ORDER BY orders.long_common_name, orders.loinc_num
;
```

`order_obs` helps characterize order/observation use but does not prove that a local
FHIR resource uses the code in a particular way.

## Selected-code validation

Validate the final numeric candidates and inspect obsolete mappings:

```sql
WITH requested(code) AS (
    VALUES
        ('<candidate LOINC code>')
)
SELECT requested.code AS requested_code,
       core.long_common_name,
       core.component,
       core.property,
       core.time_aspct,
       core.system,
       core.scale_typ,
       core.method_typ,
       core.status,
       mapping.map_to AS replacement_code,
       replacement.long_common_name AS replacement_long_common_name,
       replacement.status AS replacement_status,
       mapping.comment AS mapping_comment
FROM requested
LEFT JOIN loinc.loinc_core AS core
  ON core.loinc_num = requested.code
LEFT JOIN loinc.map_to AS mapping
  ON mapping.loinc = requested.code
LEFT JOIN loinc.loinc_core AS replacement
  ON replacement.loinc_num = mapping.map_to
ORDER BY requested.code
;
```

An absent core row is a validation failure, not evidence that the identifier should
be accepted from model memory.

## Cumulus discovery queries

`discovery__code_sources` has these columns:

```text
table_name, column_name, code, display, system
```

Profile the available Observation and DiagnosticReport code locations before choosing
`column_name` filters:

```sql
SELECT table_name,
       column_name,
       system,
       COUNT(DISTINCT code) AS distinct_code_count
FROM discovery__code_sources
WHERE table_name IN ('observation', 'diagnosticreport')
GROUP BY table_name, column_name, system
ORDER BY table_name, column_name, distinct_code_count DESC, system
;
```

Then search concrete terms across the relevant code-bearing columns:

```sql
WITH search_terms(term) AS (
    VALUES
        ('<analyte term>'),
        ('<accepted local synonym>')
)
SELECT DISTINCT
       codes.table_name,
       codes.column_name,
       codes.system,
       codes.code,
       codes.display,
       search_terms.term AS matched_search_term
FROM discovery__code_sources AS codes
CROSS JOIN search_terms
WHERE codes.table_name IN ('observation', 'diagnosticreport')
  AND LOWER(COALESCE(codes.display, ''))
          LIKE CONCAT('%', LOWER(search_terms.term), '%')
ORDER BY codes.table_name, codes.column_name, codes.system, codes.code
;
```

Run these discovery queries only when authorized. They reveal codes present at the
site but not patient-level results.

## Reconciliation

When the dedicated `loinc` schema and study discovery schema are available in the
same Athena catalog, write a reconciliation query using the concrete study database:

```sql
WITH selected_loinc(code) AS (
    VALUES ('<selected code>')
),
site_codes AS (
    SELECT DISTINCT system, code, display, table_name, column_name
    FROM <study_database>.discovery__code_sources
    WHERE table_name IN ('observation', 'diagnosticreport')
)
SELECT selected_loinc.code,
       core.long_common_name,
       core.status,
       (site_codes.code IS NOT NULL) AS observed_at_site,
       site_codes.table_name,
       site_codes.column_name,
       site_codes.display AS site_display
FROM selected_loinc
LEFT JOIN loinc.loinc_core AS core
  ON core.loinc_num = selected_loinc.code
LEFT JOIN site_codes
  ON site_codes.system = 'http://loinc.org'
 AND site_codes.code = selected_loinc.code
ORDER BY selected_loinc.code, site_codes.table_name, site_codes.column_name
;
```

Resolve `<study_database>` before delivery when it can be discovered safely. Do not
execute this reconciliation as part of local LOINC SQL generation.

## SQL file set

Create only the files needed for the request. Prefer this order:

1. `00_<slug>_discovery_profile.sql`
2. `01_<slug>_discovery_candidates.sql`
3. `02_<slug>_loinc_core_search.sql`
4. `03_<slug>_loinc_group_search.sql`
5. `04_<slug>_loinc_group_expand.sql`
6. `05_<slug>_loinc_lab_orders.sql`
7. `06_<slug>_loinc_validate_selected.sql`
8. `07_<slug>_reconcile_site_codes.sql`

State `NOT EXECUTED` in every file and in the final handoff.
