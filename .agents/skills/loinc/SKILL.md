---
name: loinc
description: >-
  Companion to the study-variable skill for designing, validating, and authoring
  LOINC-backed laboratory and DiagnosticReport valuesets in Cumulus Library studies.
  Use when a researcher asks for a lab or DiagnosticReport CSV valueset, LOINC
  codes for an analyte or indication, LOINC Groups or panels, expected UCUM units,
  missing-result interpretation or reference-range logic, reconciliation against
  discovery__code_sources, the Cumulus valueset workflow, or reviewable SQL files
  for the local cumulus-library-loinc Athena schema. Combine official LOINC APIs/web
  sources, local FHIR code discovery, and clinical context. Require human validation,
  preserve provenance and LOINC version, and never execute the generated local-LOINC
  Athena SQL.
---

# loinc — laboratory valueset companion

Use this skill with `study-variable`. Let `study-variable` own the CSV naming,
upload, cohort, union, and wide-table workflow. Use this skill to determine which
LOINC and site-local codes belong in a laboratory or DiagnosticReport valueset and
how their results may be interpreted safely.

LOINC normally produces `lab_<name>.csv` or, for report-level codes,
`diag_<name>.csv`. If a request says `rx_<name>`, confirm whether it is a typo.
Medication valuesets normally use RxNorm, not LOINC.

Read the relevant references before working:

- `references/loinc-sources.md` for terminology, APIs, groups, panels, units,
  interpretation, reference ranges, and the Cumulus workflow.
- `references/athena-query-patterns.md` before writing discovery or local LOINC SQL.

## Establish the laboratory concept

Ask only questions whose answers change code selection:

1. Define the analyte, clinical indication, and intended downstream decision.
2. Distinguish an order/panel from an individual result, and Observation from
   DiagnosticReport.
3. Specify specimen/system, property, timing, scale, and method constraints. Ask
   whether point-of-care, calculated, challenge, arterial/venous/capillary, or other
   variants belong.
4. Identify the population and setting, especially pediatric age bands, sex-related
   ranges, inpatient versus outpatient use, and site-specific laboratory methods.
5. Choose the deliverables: candidate CSV, local-code discovery, official LOINC
   verification, LOINC Athena SQL files, units, interpretation rules, reference-range
   rules, or all of them.
6. Choose `feeling lucky` for an immediate candidate set or `clarifying` for a
   narrower definition. Require review in either mode.

Do not treat a common indication as proof that every test in a customary panel
belongs in the analytic variable. Translate the clinical question into measurable
analytes first.

## Build evidence in layers

Use the following evidence order and retain provenance for every candidate:

1. **Target-site data:** inspect or query `discovery__code_sources` for
   `table_name IN ('observation', 'diagnosticreport')`. Profile `column_name` before
   filtering. Capture LOINC and local systems actually present.
2. **Official LOINC:** verify term identity, status, six-axis fit, and version with
   SearchLOINC or the official FHIR terminology service. Use `$lookup`, `$expand`,
   and `$validate-code` as appropriate. Never expose LOINC credentials.
3. **LOINC Groups and panels:** use Groups to find related term codes and panels to
   understand order/result structure. Validate membership and clinical scope.
4. **Local LOINC Athena study:** write, but never run, SELECT-only SQL against the
   dedicated `loinc` schema to search core terms, expand Groups, inspect lab orders,
   and validate status or `map_to` replacements.
5. **Clinical sources:** when suggesting indications, units, or fallback thresholds,
   consult current authoritative laboratory or clinical guidance. Label inference
   separately from terminology facts and site-observed data.

Prefer the intersection of semantically correct terms and codes observed at the
target site. Include an unobserved official code only when portability is an explicit
goal, and label it as unobserved locally.

## Select LOINC terms correctly

Evaluate all six axes: Component, Property, Time, System, Scale, and Method. Do not
collapse terms that measure different quantities merely because their displays share
an analyte name.

- Use canonical system `http://loinc.org` in valueset rows.
- Prefer active numeric LOINC term identifiers such as `718-7`.
- Use `LG...` identifiers to locate/expand Groups, not as Observation codes.
- Use `LP...` Parts for terminology navigation, not as observation valueset members.
- Use `LL...` and `LA...` identifiers for answer lists/answers, not test identities.
- Permit an atypical identifier only when local discovery proves that the source data
  uses it and the researcher explicitly wants that behavior.
- Check `loinc.map_to` for deprecated terms. Preserve the source code only when it is
  observed locally; add its active replacement when clinically equivalent.

LOINC Groups are retrieval/aggregation aids, not mapping targets. Their membership
can change by release and must be validated for the intended research use.

## Handle panels without losing result-level evidence

Keep panel/order codes separate from child observation codes. A panel code can show
that a panel was ordered or reported, but does not prove that a particular component
has a usable result. For analyte phenotypes, select the child result codes. Include
the parent panel in a separate valueset only when order/utilization is itself a study
variable.

The local `cumulus-library-loinc` Athena study does not currently load the
Panels-and-Forms tables. Use official LOINC panel resources for membership rather
than inventing Athena table names.

## Author the study-variable CSV

Follow `study-variable` and create:

```text
system,code,display
http://loinc.org,<verified-code>,<official display>
<site-local-system>,<observed-local-code>,<observed local display>
```

Use valid CSV quoting and deduplicate on `(system, code)`. Keep the official display
for LOINC and the observed display for local codes. Add optional columns only when
downstream logic consumes them. Useful, explicitly designed metadata may include
`role` (`result`, `panel_order`), `specimen_group`, `property_group`, or `tier`.
Do not add units or reference ranges as decorative metadata if the generated union
and wide tables will discard them.

Proposed codes remain candidates until a terminology/clinical reviewer approves
them and site coverage is assessed.

## Treat units, interpretation, and ranges as separate logic

Prefer, in order:

1. FHIR `Observation.interpretation` supplied by the laboratory.
2. FHIR `Observation.referenceRange`, using the matching age, sex, method, specimen,
   and context.
3. A site-approved derivation with explicit provenance and versioning.

Use UCUM-compatible units and compare numeric values only after confirming compatible
property, specimen, and units or performing a validated conversion. Never infer a
universal normal range from a LOINC code. Pediatric reference ranges commonly vary by
age and other factors. When required inputs are missing or incompatible, return
`unknown`/`not classifiable` rather than forcing `normal` or `abnormal`.

Keep raw and derived fields side by side. Name derived fields explicitly, for example
`derived_interpretation_code`, `derived_rule_id`, and `derived_rule_source`. Do not
overwrite the laboratory's interpretation.

## Use Cumulus valueset construction conditionally

Inspect the installed Cumulus version and its valueset workflow before configuring
it. The documented default expands UMLS/RxNorm drug ingredients and is not
automatically a LOINC laboratory grouping engine. Use it only when the configured
seed sources, installed terminology studies, and traversal rules support the desired
LOINC use case. Otherwise author the reviewed CSV through `study-variable`.

Keep any workflow configuration in the study manifest dependency order. Record seed
keywords, external valueset identifiers, expansion rules, terminology versions, and
the review decision.

## Write SQL files without executing them

For local LOINC Athena exploration:

1. Ask for or choose a repository-local output directory, defaulting to
   `sql/loinc/` when no convention exists.
2. Write concrete, SELECT-only `.sql` files using the actual dedicated schema and
   columns documented in `references/athena-query-patterns.md`.
3. Include a header with purpose, analyte, assumptions, search terms, expected
   output grain, source tables, and the LOINC version to be checked at execution.
4. Generate separate files for core-term search, Group expansion, lab-order search,
   selected-code validation, and discovery reconciliation when each is relevant.
5. Use placeholders only for environment-specific database/catalog names, clearly
   marking each one. Resolve clinical search terms before delivery.
6. Do **not** connect to or execute against the local LOINC Athena database. Do not
   create tables in the reserved `loinc` schema.

Read-only queries against the target study's `discovery__code_sources` may be run
only when the researcher requests local discovery and the authorized database
connection is already available. Otherwise write the discovery SQL for them.

## Validate and hand off

Before completion:

- Validate CSV structure, canonical systems, code format, duplicate keys, active
  status, deprecated mappings, six-axis scope, and panel-versus-result separation.
- Reconcile official candidates with target-site codes and identify unmatched local
  codes for manual mapping.
- Review units and any derived interpretation/range rules independently of code
  membership.
- Confirm all local LOINC SQL files are unexecuted and contain no credentials or PHI.
- Instruct the researcher to regenerate `study_variable` and
  `study_variable_wide`; do not run those generators unless requested.

Report candidate/approved counts, local coverage, unverified codes, terminology
version, generated SQL paths, interpretation assumptions, and remaining reviewer
decisions.
