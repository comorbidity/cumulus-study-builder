# LOINC sources and clinical interpretation

## Contents

- Official terminology resources
- LOINC term structure
- Groups and panels
- Units, interpretations, and reference ranges
- Cumulus valueset workflow
- Evidence and provenance labels

## Official terminology resources

Prefer primary sources:

- LOINC FHIR terminology service: <https://loinc.org/fhir/>
- LOINC Groups: <https://loinc.org/groups/>
- LOINC Panels and Forms: <https://loinc.org/panels./>
- LOINC Knowledge Base: <https://loinc.org/kb/>
- Cumulus workflow reference: <https://docs.smarthealthit.org/cumulus/library/workflows.html>
- Cumulus valueset workflow: <https://docs.smarthealthit.org/cumulus/library/workflows/valueset.html>
- Cumulus LOINC study: <https://github.com/smart-on-fhir/cumulus-library-loinc>

The LOINC FHIR service requires a LOINC account. Never place the username or password
in a URL, source file, command output, or chat response. Use the supported secure
credential mechanism.

Useful FHIR operations include:

```text
GET https://fhir.loinc.org/CodeSystem/$lookup?system=http://loinc.org&code=<code>
GET https://fhir.loinc.org/ValueSet/$expand?url=http://loinc.org/vs/<LG-or-LL-id>
GET https://fhir.loinc.org/ValueSet/<LG-id>/$validate-code?system=http://loinc.org&code=<code>
```

Record the LOINC version returned by the service. A current unversioned expansion can
change as new terms are added to a Group. Pin or record the release used for a
reproducible study.

## LOINC term structure

Select a term using all six axes:

| Axis | Question |
|---|---|
| Component | What analyte or observation is measured? |
| Property | What kind of quantity is measured, such as mass concentration? |
| Time | Is this a point, interval, challenge, or other timing? |
| System | What specimen or subject is measured? |
| Scale | Is the result quantitative, ordinal, nominal, narrative, or another scale? |
| Method | Is a method specified and does the study require or exclude it? |

Displays alone are insufficient. For example, the same analyte may have mass and
molar concentration terms, different specimens, calculated versus measured terms,
and point-of-care versus laboratory methods. Include each only when it answers the
same study question or explicitly categorize the differences.

Identifier roles:

| Prefix/form | Role | Valueset use |
|---|---|---|
| Numeric check-digit, e.g. `718-7` | LOINC term | Normal test/report code candidate |
| `LG...` | LOINC Group | Expand to member terms; do not map data to the Group |
| `LP...` | LOINC Part | Navigate/search terminology; not normally an Observation code |
| `LL...` | Answer list | ValueSet for coded answers |
| `LA...` | Answer | Coded result value, not test identity |

## Groups and panels

LOINC Groups aggregate terms that may be equivalent for a particular retrieval,
display, or research purpose. Use a Group as a candidate generator. Verify its axes,
members, active status, intended context, and release before adopting all members.
LOINC explicitly cautions that Groups are not mapping targets and require validation
for patient-care or research use.

Panels are enumerated collections with required, optional, conditional, and nested
members. Distinguish:

- the panel/order code, which indicates a collection was ordered or represented;
- child Observation codes, which identify individual result values;
- an interpretation/impression term, which may summarize multiple results.

Do not infer that every child was resulted because a parent panel appears. Do not use
only the parent code when the phenotype needs a numeric analyte value.

The current `cumulus-library-loinc` subset loads Groups but not the Panels-and-Forms
tables. Retrieve panel structure from official LOINC resources rather than querying a
nonexistent local table.

## Units, interpretations, and reference ranges

LOINC identifies the observation, not a universal normal range. Use UCUM syntax for
machine-comparable units and preserve meaningful bracket characters. Confirm that a
unit is compatible with the term's Property and System before comparison or
conversion.

Use this precedence:

1. Laboratory-provided FHIR `Observation.interpretation`.
2. Applicable FHIR `Observation.referenceRange`.
3. Site-approved derived logic from an authoritative source.

An applicable range may depend on age, sex, pregnancy status, specimen, fasting
state, collection timing, assay, platform, and laboratory. Pediatric ranges often
change across narrow age bands. A methodless LOINC code does not erase method-related
range differences.

For derived interpretation rules:

- preserve raw value, unit, interpretation, and reference range;
- require a compatible unit or validated conversion;
- version the rule and cite its clinical source;
- state the population and applicability criteria;
- emit unknown when inputs do not support classification;
- never replace a laboratory-supplied interpretation silently.

The LOINC panel guidance recommends transmitting abnormal interpretation in the
result's interpretation/abnormal-flag field when available rather than as a separate
observation.

## Cumulus valueset workflow

The Cumulus valueset workflow can combine keyword seeds, VSAC valuesets, UMLS source
vocabularies, and configurable relationship-expansion rules. Its documented default
use case expands drugs from ingredients using UMLS/RxNorm relationships.

Before using it for LOINC:

1. Inspect the installed Cumulus version and workflow schema.
2. Verify that the necessary terminology study and LOINC source vocabulary are
   installed and queryable.
3. Define expansion rules appropriate to the laboratory concept rather than reusing
   drug-ingredient rules.
4. Review the expanded set and preserve seed/source provenance.
5. Fall back to a curated `lab_<name>.csv` when the workflow does not support the
   intended LOINC relationship semantics.

Do not promise that the workflow understands LOINC Groups or panels unless the
installed implementation demonstrates that capability.

## Evidence and provenance labels

Track candidates using labels such as:

- `official_exact`: official active term matching all required axes;
- `official_group_member`: discovered through a reviewed LOINC Group;
- `official_panel_member`: discovered through a reviewed panel structure;
- `site_observed_loinc`: exact LOINC code present in discovery data;
- `site_observed_local`: local code requiring manual mapping or intentional inclusion;
- `deprecated_source`: locally observed retired code with a `map_to` candidate;
- `llm_suggested_unverified`: candidate not yet confirmed by an authoritative source.

Do not write these as CSV columns unless downstream code consumes them. Keep them in
the review record or SQL result instead.

