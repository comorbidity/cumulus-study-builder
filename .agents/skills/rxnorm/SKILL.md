---
name: rxnorm
description: >-
  Companion to the study-variable skill for authoring rx_ medication valuesets
  (rx_class CSVs) for a cumulus-study-builder study. It builds coded
  drug-class valuesets class-first: pick a class by mechanism of action (MoA),
  established pharmacologic class (EPC), or ATC, expand to ingredients then to
  clinical drugs and products (SCD/SBD/GPCK/BPCK), and emit RxNorm rxcui codes plus
  optional NDC. Use whenever someone wants to create or expand a medication valueset,
  a drug class, an ingredient set, or a treatment-line rx_class. It leads with the
  RxNorm REST and RxClass APIs and internal RxNorm knowledge (generic,
  brand, other names), then WRITES but never executes SQL against local
  cumulus-library-rxnorm and cumulus-library-umls Athena tables, and validates
  real-data presence via the CORE discovery__code_sources table for medicationrequest
  and medicationdispense. Offer two modes, feeling-lucky or curated. The rx_ CSV drops
  into the study-variable stage. proposed rxcui codes are candidates a human verifies.
---

# rxnorm — medication valueset authoring (companion to study-variable)

This skill helps a researcher build **rx_ medication valuesets** — the coded drug
sets that the `study-variable` skill turns into `example__cohort_rx_*` tables and
the therapy-line engine in the `eligible` skill consumes. It is the medication
specialist that `study-variable` delegates to for the `rx` aspect. Replace `example`
with your study prefix.

**Working principle: this skill WRITES SQL, it does not RUN it.** It leads with
RxNorm/RxClass knowledge and the public APIs, then hands the researcher SQL to
execute against their own Athena. It never executes queries itself.

## Optional online lookup with `UMLS_API_KEY`

Check whether `UMLS_API_KEY` is present without printing or returning its value. Use
the online path for fast candidate discovery when network access is available:

1. Use ordinary RxNav RxNorm/RxClass REST endpoints first. They normally require no
   key and should not receive `UMLS_API_KEY`.
2. When the key is present, additionally use UTS REST searches restricted to
   `sabs=RXNORM`, source atoms/relations, and VSAC expansions when appropriate. This
   can resolve current source identifiers and synonyms without waiting for a local
   Athena terminology build.
3. Supply the key only to endpoints that require it. The unusual RxNav proprietary
   information endpoint may accept the UTS key as a Bearer credential; do not send
   the key to other RxNav endpoints.

Never interpolate the key into a displayed URL or shell command, and never write it
to CSV, SQL, logs, caches, or chat. Send only terminology search terms or codes, never
PHI. Respect API rate limits. Record endpoint, RxNorm/UMLS release, class axis,
parameters, and retrieval date. Treat online results as candidates and still run the
site-presence and human-review steps. If online access fails, write the local
RxNorm/UMLS Athena SQL instead; the local release remains the preferred reproducible
snapshot for a publishable derivation.

## What it produces

A study-variable rx valueset CSV: `spreadsheet/rx_class_<name>.csv` (or
`rx_<name>.csv`), header **`keyword,system,code,display`**:

- `keyword` — the ingredient / search term / class label that seeded the row (the
  rx_class convention. leads the header).
- `system` — RxNorm `http://www.nlm.nih.gov/research/umls/rxnorm` (add rows in NDC or
  a local system only if your data uses them — check with the presence step below).
- `code` — the RxNorm `rxcui`.
- `display` — the RxNorm concept string (`str`).

One code per row. The cohort join in study-variable matches on `code` + `system`, so
`code`/`system` must match how medications appear in `core__medicationrequest` /
`core__medicationdispense`. That is what the discovery presence check verifies.

## Class-first method (the default)

A drug class is defined once, then expanded down the RxNorm graph:

1. **Name the class** by one of: **MoA** (mechanism of action, e.g. "tumor necrosis
   factor blocker"), **EPC** (established pharmacologic class), or **ATC** (Anatomical
   Therapeutic Chemical, e.g. `L04AB` TNF-alpha inhibitors). These are RxClass class
   types. pick the one that matches how the researcher thinks about the class.
2. **Class → ingredients.** Resolve the class to its member **ingredients**
   (`IN` / `MIN` / `PIN`) via RxClass `classMembers`, or via the rxnorm tables.
3. **Ingredients → clinical drugs and products.** Expand each ingredient to
   prescribable/dispensable concepts — `SCD`, `SBD`, `GPCK`, `BPCK` (and `SCDC` /
   `SBDC` components) — following the RxNorm relationships (`has_ingredient`,
   `consists_of`, `has_form`, `tradename_of`, …). This captures generic AND brand AND
   combination products, and their `other names`.
4. **Emit rxcui + display**, tagged with the seeding `keyword`. optionally attach NDC
   (see the reference) if your medications are NDC-coded.

Single-ingredient or named-drug valuesets are the same pipeline starting at step 2.

## The derivation ladder (APIs and knowledge first, then written SQL)

Use the cheapest sufficient rung. escalate for completeness or reproducibility:

1. **Internal RxNorm knowledge + online APIs.** Fast first pass. Map the class to
   ingredients, brands, products, and rxcui using public RxNorm/RxClass endpoints
   (`rxclass`, `/rxcui`, `/related`, `/approximateTerm`) and, when
   `UMLS_API_KEY` is present, UTS/VSAC as described above. Good for a candidate
   valueset in one pass.
2. **Write SQL against the local terminology (do not run it).** For reproducibility
   and completeness, author SQL against the Athena `rxnorm` schema
   (`rxnorm__rxnconso`, `rxnorm__rxnrel`, `rxnorm__rxnsat`) and, for cross-vocabulary
   (ATC, NDC, cross-SAB), the `umls` schema (`umls__MRCONSO`, `umls__MRREL`,
   `umls__MRSAT`). Hand the researcher the query to run. The reference has the seed →
   expand → attach-NDC query patterns and the RELA relationship list.
3. **Validate against real data — always.** Write a query that joins the candidate
   rxcui set to `discovery__code_sources` filtered to
   `table_name IN ('medicationrequest','medicationdispense')`. Codes that never appear
   in the dataset link nothing. this tells the researcher which candidates are real
   for their data and whether their data is even RxNorm-coded (vs NDC / local).

## Two modes — ask which up front

Mirror the study-variable skill:

- **"I'm feeling lucky"** — generate a best-effort candidate `rx_class_<name>.csv`
  now from RxNorm/RxClass knowledge (class → ingredients → common products, rxcui +
  display). Present it, and give the researcher the presence-check SQL to run.
- **"Curated"** — elicit the class definition before writing: which class axis
  (MoA / EPC / ATC) and the exact class; include/exclude combination products; brand
  names in scope; routes of administration to keep or drop (oral vs injectable, etc.);
  precise vs base ingredient. Then author the CSV and the reproducible seed/expand
  SQL. This is the path for a publishable, defensible valueset.

In **both** modes end with the same caveat: **the rxcui codes are candidates.** RxNorm
is versioned (monthly). rxcui can be retired or remapped, and TTY choice changes
breadth. Verify against an authoritative source (the RxNav browser, VSAC, RxClass) and
against `discovery__code_sources`. Do not present generated codes as validated.

## When to use the Cumulus valueset workflow instead

For a **highly curated, portable, PR-reviewable** valueset — the level of the
`cumulus-library-opioid-valueset` — point the researcher at the Cumulus **valueset
workflow** (`config_type = "valueset"`): it seeds from VSAC stewards, UMLS stewards,
and a `keyword_file`, then expands by traversing UMLS `MRREL` with configurable
`REL`/`RELA` rules, producing `<prefix>__valuesets` and `<prefix>__combined_ruleset`
(the researcher extracts the distinct concepts as the drug list). That is the
heavy-duty, multi-source, agreement-checked path; this skill's rx_ CSV is the direct,
study-embedded path. The reference covers the workflow config and how to flatten its
output back into an `rx_class_<name>.csv`.

## Handoff to study-variable

The rxnorm skill authors the CSV (and the SQL to derive/validate it). It does not run
the generators. Once `spreadsheet/rx_class_<name>.csv` exists, hand back to
`study-variable`: it registers the file and regenerates the rx cohort + union + wide
tables (`python -m cumulus_study_builder.tools.study_variable` +
`study_variable_wide`). A well-named rx_class then flows into the `eligible` therapy
lines automatically.

## Rules

- Author CSVs and SQL. never execute SQL, and never hand-edit generated study tables.
- Prefer RxNorm as the `system`. add NDC/local rows only when the presence check shows
  the data uses them.
- Prose comments separate sentences with periods, not semicolons (house style).

See `references/rxnorm_reference.md` for the rxnorm/umls table schemas and TTY/RELA
meanings, the RxClass class types and REST endpoints, the seed → expand → NDC →
presence-check SQL patterns, the discovery presence check, and the valueset-workflow
config.

## Worked example

"Build an anti-TNF drug class for the rx aspect." → class axis = EPC/MoA "tumor
necrosis factor blocker" (ATC `L04AB`). ingredients: infliximab, adalimumab,
etanercept, certolizumab pegol, golimumab. expand each to SCD/SBD/GPCK/BPCK products
(generic + brand: Remicade, Humira, Enbrel, Cimzia, Simponi). emit
`spreadsheet/rx_class_anti_tnf.csv` (`keyword,system,code,display`) with rxcui +
str, then give the researcher the RxNorm expansion SQL and the
`discovery__code_sources` presence-check SQL to run, and note the codes need
verification. Hand back to study-variable to build.
