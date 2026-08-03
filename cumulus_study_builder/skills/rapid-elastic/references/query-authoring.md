# Query authoring reference

Use this reference while creating or reviewing `query_topics.tsv` for a Cumulus
study backed by `rapid-elastic`.

## File contract

Use a tab-delimited UTF-8 file with this exact header:

```text
topic\tquery
```

Each remaining physical line defines one query. `rapid_elastic.pipeline.pipe_batch`
loads the file into a topic-to-query mapping and emits one CSV named for each topic.
Consequently, topics must be unique and safe as stable table/file identifiers.

Use this structural pattern:

```text
topic\tquery
dx_condition_tier1\tnote:("full condition name" OR "accepted synonym")
dx_condition_tier2\t(note:("suggestive finding") AND note:(condition OR diagnosis))
```

The examples are syntax illustrations only. Replace their terms and tier meanings
with a clinician-reviewed definition for the target study.

## Topic naming

- Use lowercase snake case.
- Prefer a meaningful family prefix such as `dx_`, `rx_`, `surgery_`, or a named
  extraction task when downstream SQL parses that family.
- Add `_tier1`, `_tier2`, and similar suffixes only after defining their semantics.
- Keep a topic name stable after result CSVs or Athena tables depend on it.
- Check whether downstream SQL joins `topic = variable`; if so, match the coded FHIR
  study-variable name exactly where intended.

Observed study patterns include disease-specific `dx_<name>` topics and broader
families such as `diagnosis_tier1a`, `diagnosis_tier2`, `surgery_tier1`, and
`medication_tier3`. These are study conventions, not universal rapid-elastic rules.

## Expression design

Use the syntax already accepted by the study's Elasticsearch configuration:

- Scope text terms with the configured note field, commonly `note:`.
- Quote multiword phrases: `note:"ulcerative colitis"`.
- Group alternatives: `note:("term one" OR "term two" OR acronym)`.
- Group concepts before combining them:
  `(note:(name OR synonym) AND note:(diagnosis OR confirmed))`.
- Use uppercase `AND`, `OR`, and `NOT` and explicit parentheses. Do not depend on
  implicit precedence in a long clinical query.
- Preserve phrase-slop forms such as `"bowel wall thickening"~4` only when they are
  deliberate and supported by the configured query parser.

Build from concept blocks rather than one undifferentiated synonym list:

1. Canonical names and spelling variants.
2. Accepted historical names and eponyms.
3. Abbreviations, paired with context when ambiguous.
4. Diagnostic language or evidence terms.
5. Explicit exclusions or competing concepts, when retrieval precision requires
   them.

Prefer several named topics with documented meanings over one opaque query when the
downstream analysis needs to distinguish evidence strength or domain.

## Clinical review prompts

Ask the researcher or clinical reviewer:

- Does the query retrieve confirmed disease, suspected disease, workup, history, or
  all of these?
- Are family history, negated mentions, rule-out language, and educational boilerplate
  in or out?
- Which acronyms are ambiguous in this corpus?
- Do medication mentions mean current exposure, historical exposure, failure,
  adverse effect, or any mention?
- Do tiers represent specificity, certainty, source type, or review priority?
- Is high recall acceptable because chart review follows, or must the search itself
  be more specific?

Record the answers in the topic names, adjacent study documentation, or downstream
task definition. The TSV schema itself has no description column.

## Validation checklist

- Exact `topic` and `query` header.
- Exactly two tab-separated cells per row.
- No empty or duplicate topic.
- No empty query.
- One physical line per query.
- Balanced parentheses and quotes.
- Every intended term remains inside the expected field scope.
- Boolean tree matches the researcher's verbal definition.
- Topic names match downstream task, tier, and FHIR-variable logic.
- Human expert reviewed terminology and exclusions.

The query-tree utility is useful for visual inspection because it expands nested
`AND`, `OR`, and `NOT` structure and can show fields on groups or leaves. It is not
an Elasticsearch server validator and does not establish clinical validity.

## Pipeline map

```text
spreadsheet/query_topics.tsv
        |
        v
tools/elastic_query.py -> rapid_elastic.pipeline.pipe_batch
        |
        v
sibling elastic_output/<topic>.csv
        |
        v
tools/elastic_output.py
        |
        +-> elastic_output/file_upload_elastic.toml
        +-> elastic_output.toml
        +-> athena/<prefix>__elastic_*.sql from template/ sources
```

The output generator is study-specific. For example, one observed study renders a
general union and a FHIR-versus-Elastic diagnosis comparison. Another renders a
general union plus task, aspect, and tier tables. Always inspect the current study's
generator and templates rather than copying either layout.

## Cached-output rule

`rapid_elastic.pipeline.pipe_query` skips a topic when `<topic>.csv` or
`<topic>.csv.gz` already exists in the output directory. After changing a query:

1. Detect the existing result.
2. Tell the researcher that it is stale relative to the new definition.
3. Ask whether to preserve it, archive it, choose a new output directory, or replace
   it.
4. Perform no deletion or overwrite without explicit authorization.

## Data handling

Result CSVs can contain FHIR references and note metadata. Treat them as clinical
data, keep them in the authorized environment, and avoid copying them into the
repository or conversation. Never display environment-variable values for
`ELASTIC_USER` or `ELASTIC_PASS`.
