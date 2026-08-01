---
name: rapid-elastic
description: >-
  Design, review, run, and integrate rapid-elastic clinical-note retrieval for a
  Cumulus Library study. Use when a researcher wants to create or revise a
  query_topics.tsv topic/query file, translate clinical concepts and synonyms into
  fielded KQL/query-string expressions, inspect Boolean query trees, run the
  project's elastic_query.py stage, register result CSVs through elastic_output.py,
  or build downstream Athena elastic union, comparison, or task tables. Also use to
  audit topic naming, tiers, query precision/recall, cached results, stage manifests,
  and generated Elastic SQL. Require human review of clinical terminology. Protect
  credentials and note-derived PHI. Never hand-edit generated TOML or SQL artifacts.
---

# rapid-elastic — clinical-note retrieval pipeline

Guide a researcher from a clinical retrieval question to reviewed Elastic topics,
search-result CSVs, and optional Athena tables. Treat this as a retrieval workflow,
not a computable phenotype: a text hit is evidence for review and does not by itself
establish diagnosis, treatment, timing, or eligibility.

Read `references/query-authoring.md` before authoring or materially revising query
topics.

## Ask before doing heavy work

Ask only the unresolved questions that change the result:

1. Identify the target study root and study prefix.
2. Choose the task: author/revise topics, audit syntax, run the live search,
   integrate existing CSV output, or complete the full workflow.
3. Define the clinical boundary, required synonyms, exclusions, tier meanings, and
   desired precision-versus-recall balance.
4. Confirm whether topic names must align with FHIR study-variable names or other
   downstream Athena joins.
5. Before a live search, confirm secured network access, intended output directory,
   and whether existing topic CSVs should be retained, archived, or deliberately
   replaced.

Offer a recommended default when useful. Do not ask again for facts already present
in the request or repository.

## Discover the study's implementation

From the study root:

1. Read local instructions and the top-level manifest.
2. Locate `spreadsheet/query_topics*.tsv`, `tools/elastic_query.py`,
   `tools/elastic_output.py`, `elastic_query.toml`, `elastic_output.toml`,
   `template/elastic_union*.sql`, and any query-tree utility.
3. Inspect the project's actual package name, tablespace prefix, output-directory
   helper, manifest registration, and generator behavior. Do not assume that two
   Cumulus studies have identical downstream tables.
4. Inspect the installed or sibling `rapid-elastic` package when behavior is unclear.
   Its `pipeline.pipe_batch()` reads topic/query pairs, runs one query per topic, and
   writes one result CSV per topic.
5. Trace every prospective edit to its owner. If a builder rewrites a file, edit its
   source and regenerate rather than patching the output.

## Respect artifact ownership

Use this default ownership model, then verify it against the target study:

| Artifact | Role | Default treatment |
|---|---|---|
| `spreadsheet/query_topics.tsv` | Curated topic/query definitions | Edit after clinical confirmation |
| `tools/elastic_query.py` | Study adapter that calls `rapid_elastic.pipeline` | Reuse; change only for explicit integration work |
| `elastic_query.toml` | Registers the potentially long-running query action | Verify ownership before editing |
| sibling `elastic_output/*.csv` | Note-search results, potentially containing PHI | Runtime data; do not commit or expose |
| `tools/elastic_output.py` | Registers result CSVs and renders downstream artifacts | Generator/source code |
| `elastic_output/file_upload_elastic.toml` | CSV upload manifest | Generated |
| `elastic_output.toml` | Output-stage manifest | Generated when produced by `elastic_output.py` |
| `athena/<prefix>__elastic_*.sql` | Union, comparison, or task tables/views | Generated when rendered from tools/templates |
| `template/elastic_union*.sql` | Structural SQL source | Edit only when the requested table contract changes |

Never modify Python, templates, or generated artifacts merely to author topics.

## Author query topics

1. Keep exactly two TSV columns: `topic` and `query`.
2. Use unique, stable, lowercase snake-case topic names. Align names with downstream
   variables when the union/comparison SQL joins on topic or variable.
3. Define tier semantics explicitly. Do not infer that `tier1`, `tier2`, and `tier3`
   mean the same thing across studies.
4. Build expressions with explicit fields, parentheses, quoted multiword phrases,
   and uppercase Boolean operators. Preserve intentional phrase slop such as
   `"phrase"~N` when the target query parser supports it.
5. Anchor ambiguous abbreviations with contextual terms. Separate confirmed-name,
   suggestive-evidence, and broad-recall topics when the research design needs those
   distinctions.
6. Keep one physical TSV row per topic. Do not place literal tabs or newlines inside
   a query cell.
7. Treat suggested terms as candidates. Require a clinician or domain expert to
   verify synonyms, acronyms, historical names, exclusions, and tier placement.

Do not copy a large disease vocabulary from another study merely because its syntax
is valid. Reuse its structural patterns, then curate content for the target question.

## Validate before running

Perform all applicable checks:

- Parse the TSV and require the exact header, two fields per row, nonempty topics and
  queries, and unique topics.
- Check balanced grouping, quoting, field scope, and Boolean precedence.
- Run the study's `elastic_query_print_tree.py` or equivalent on every changed topic
  when available. Treat parse failures as blockers. Use the tree as a readability
  aid, not proof that Elasticsearch will accept or clinically interpret the query.
- Compare topic names with downstream FHIR variables and task/tier parsing logic.
- Show a compact topic list and summarize the intended tier/boundary for human
  confirmation. Do not print thousands of terms unless requested.

## Run the live query only when requested

Before execution:

1. Verify `ELASTIC_HOST`, `ELASTIC_USER`, and `ELASTIC_PASS` are set without printing
   their values. Respect `ELASTIC_OUTPUT` or the study's explicit output path.
2. Confirm the researcher is connected to the authorized VPN/firewall environment.
3. Inspect existing CSVs. `rapid-elastic` skips a topic when its output CSV or
   compressed CSV already exists, so a changed query can otherwise appear to run
   while retaining stale results.
4. Never delete or overwrite an existing output silently. Prefer a new output
   directory or archive the old file after approval.

Run the project's adapter, normally its `tools/elastic_query.py`, or use the
installed `rapid-elastic --topics <file> --output <dir>` interface when the study has
no adapter. Expect the operation to be long-running. Report per-topic completion and
failures without displaying note text or credentials.

## Build downstream Athena artifacts optionally

After reviewed output CSVs exist:

1. Run the study's `tools/elastic_output.py` generator.
2. Confirm it registered the intended CSVs, regenerated its upload/stage manifests,
   and rendered only the expected Athena artifacts.
3. Inspect the study-specific contract. One study may produce
   `elastic_union` plus `elastic_union_dx`; another may produce `elastic_union` plus
   hand-authored task/aspect/tier tables.
4. Confirm table grain and keys. Typical hit-level fields include `subject_ref`,
   `encounter_ref`, `note_ref`, and `document_title`; union or hydration steps can
   change the effective grain.
5. Run the broader study builder or Cumulus build only when requested and after the
   stage is registered in dependency order.
6. Review the diff. Flag disappearing topics, unrelated generated churn, changed
   table names, or output files not represented in the TSV.

## Protect clinical data

- Never place credentials in commands, TOML, TSV, logs, commits, or chat output.
- Treat result CSVs and note-derived fields as potentially identifiable clinical
  data. Keep them in the authorized output location and out of source control.
- Summarize counts and paths instead of reproducing note text.
- Do not describe a retrieval hit as a confirmed case without a separate validated
  case-definition or chart-review step.

## Complete the handoff

Report:

- the study, topic file, and topics added/changed;
- the clinical boundary and tier semantics confirmed by the researcher;
- structural and Boolean-tree validation results;
- whether the live query ran, was skipped, or remains intentionally pending;
- whether cached output may be stale;
- generated manifests and Athena artifacts, if any;
- the grain of each downstream table and the next authorized build step.

