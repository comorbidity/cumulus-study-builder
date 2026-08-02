# rxnorm reference

Technical detail for authoring rx_ medication valuesets: the local terminology
schemas, RxNorm term types and relationships, RxClass, the REST endpoints, the
seed → expand → NDC → presence-check SQL patterns (write, do not execute), the
discovery presence check, and the Cumulus valueset workflow. Replace `example` with
your study prefix.

## Local terminology in Athena

Two installable Cumulus studies load terminology into their **own schemas**. They
require a UMLS/NLM API key and are built separately (`pip install
cumulus-library-rxnorm` / `-umls`, then `cumulus-library build --target rxnorm`
with `--umls-key`). Do not run these. write SQL the researcher runs against them.

### `rxnorm` schema (from cumulus-library-rxnorm — RxNorm RRF)

Tables are `rxnorm__<rrf_stem>`. The ones you need:

| Table | Key columns | Use |
|---|---|---|
| `rxnorm__rxnconso` | `rxcui`, `str`, `sab`, `tty`, `code`, `suppress` | Concept names/atoms. filter `sab='RXNORM'`, pick by `tty`. |
| `rxnorm__rxnrel` | `rxcui1`, `rxcui2`, `rel`, `rela`, `rui` | Concept-to-concept relationships (the expansion graph). |
| `rxnorm__rxnsat` | `rxcui`, `atn`, `atv`, `sab` | Attributes. `atn='ATC'`, `atn='NDC'`, etc. |
| `rxnorm__rxnsty` | `rxcui`, `tui`, `sty` | Semantic types. |

### `umls` schema (from cumulus-library-umls — UMLS Metathesaurus)

Use for cross-vocabulary (ATC, NDC, SNOMED, cross-SAB) beyond RxNorm.

| Table | Key columns | Use |
|---|---|---|
| `umls__MRCONSO` | `cui`, `aui`, `str`, `sab`, `tty`, `code`, `suppress` | Atoms across all source vocabularies. |
| `umls__MRREL` | `cui1`, `aui1`, `rel`, `rela`, `cui2`, `aui2`, `rui`, `sab` | Cross-vocab relationships (the valueset-workflow traversal table). |
| `umls__MRSAT` | `cui`, `code`, `atn`, `atv`, `sab` | Attributes (e.g. ATC level, NDC). |
| `umls__MRSTY` | `cui`, `tui`, `sty` | Semantic types. |
| `umls__mrconso_drugs`, `umls__mrrel_is_a` | derived | Convenience drug/is-a subsets the study ships. |

## RxNorm term types (TTY) — pick the breadth you want

| TTY | Meaning | Role |
|---|---|---|
| `IN` | Ingredient | class-member anchor |
| `PIN` | Precise ingredient (e.g. a salt) | precise anchor |
| `MIN` | Multiple ingredients | combination anchor |
| `BN` | Brand name | brand anchor |
| `SCDC` / `SBDC` | Clinical / branded drug component | ingredient+strength |
| `SCD` | Semantic clinical drug (generic, prescribable) | the usual target |
| `SBD` | Semantic branded drug | branded prescribable |
| `GPCK` / `BPCK` | Generic / branded pack | packs |
| `DF` / `DFG` | Dose form / dose-form group | route/form filtering |

A generic-only valueset = `SCD` + `GPCK`. add `SBD` + `BPCK` for brands.

## RxNorm relationships (RELA) — the expansion graph

`rxnorm__rxnrel.rela` (directional. each has an inverse):

- `has_ingredient` / `ingredient_of`
- `has_precise_ingredient` / `precise_ingredient_of`
- `consists_of` / `constitutes` (SCD ↔ SCDC components)
- `has_dose_form` / `dose_form_of`, `has_doseformgroup`
- `tradename_of` / `has_tradename` (generic ↔ brand)
- `contains` / `contained_in` (packs)
- `has_form` / `form_of`, `has_part` / `part_of`
- `isa` / `inverse_isa` (ATC/class hierarchy)

Ingredient → prescribable expansion typically follows `ingredient_of` /
`inverse_isa` / `consists_of` / `has_tradename` to reach `SCD`/`SBD`/`GPCK`/`BPCK`.

## RxClass — class axes and how to resolve members

RxClass groups drugs by class. The **class types** you will use:

- `ATC1-4` — Anatomical Therapeutic Chemical (WHO). e.g. `L04AB` = TNF-alpha inhibitors.
- `MOA` — mechanism of action.
- `EPC` — established pharmacologic class (FDA).
- `PE` — physiologic effect. `CHEM` — chemical structure. `PK` — pharmacokinetics.
- `TC` — therapeutic class (VA). `DISEASE` (`may_treat` / `ci_with`). `VA`, `SCHEDULE`.

`relaSource` (who asserted the class): `ATC`, `MED-RT` / `NDFRT` (MoA/EPC/PE),
`DAILYMED`, `FDASPL`, `FMTSME`, `VA`.

REST (RxClass): `GET /REST/rxclass/class/byName?className=...&classTypes=MOA` →
classId; `GET /REST/rxclass/classMembers?classId=L04AB&relaSource=ATC&ttys=IN` →
member ingredients; `GET /REST/rxclass/class/byRxcui?rxcui=...` → a drug's classes.

## RxNorm REST endpoints (the API-first rung)

Base `https://rxnav.nlm.nih.gov/REST`:

- `/rxcui.json?name=adalimumab&search=2` → rxcui for a name (approximate with `search`).
- `/rxcui/{rxcui}/related.json?tty=SCD+SBD+GPCK+BPCK` → products for an ingredient.
- `/rxcui/{rxcui}/allrelated.json` → everything related.
- `/approximateTerm.json?term=humira` → fuzzy name → rxcui.
- `/drugs.json?name=infliximab` → drugs by name grouped by TTY.
- `/rxcui/{rxcui}/ndcs.json` → NDCs for a concept.
- RxClass `/rxclass/classMembers.json?...` as above.

No key is required for ordinary RxNav REST. It is the fast first pass. The local
tables are the reproducible, offline, versioned pass.

### Optional UTS and VSAC lookup with `UMLS_API_KEY`

When `UMLS_API_KEY` is exported, a secure client may also make read-only calls to the
UMLS REST and VSAC services:

- UTS base: `https://uts-ws.nlm.nih.gov/rest`.
- Search current RxNorm source content with `/search/current`, `sabs=RXNORM`, and a
  source-oriented `returnIdType` such as `sourceUi` when the desired output is an
  RxNorm identifier rather than a UMLS CUI.
- Use `/content/current/.../atoms` and source relations to inspect source names and
  relationships. Use VSAC FHIR expansion for a known reviewed value-set OID.
- The Cumulus Library CLI also recognizes `UMLS_API_KEY` as the environment-variable
  equivalent of `--umls-key` for VSAC and terminology download/build workflows.

Read the key from the environment only inside the authenticated client. Never echo it,
place it in a displayed request URL, or persist it in SQL, CSV, response provenance,
logs, or caches. Record the resolved UMLS/RxNorm release because `current` changes.

The RxNorm proprietary-information endpoint is the exception to the usual key-free
RxNav rule: it can use the UTS API key as an `Authorization: Bearer` credential for
licensed source atoms. Do not send that header to ordinary RxNorm/RxClass endpoints.
Respect RxNav and UTS rate limits and terms of service.

## SQL patterns (WRITE these for the researcher. do not run them)

Seed — ingredient name to rxcui:

```sql
SELECT DISTINCT rxcui, str, tty
FROM   rxnorm.rxnorm__rxnconso
WHERE  sab = 'RXNORM' AND suppress = 'N'
  AND  tty IN ('IN','MIN','PIN')
  AND  LOWER(str) LIKE '%adalimumab%';
```

Class members by ATC (RxNorm attributes):

```sql
SELECT DISTINCT c.rxcui, c.str, c.tty
FROM   rxnorm.rxnorm__rxnsat  s
JOIN   rxnorm.rxnorm__rxnconso c ON c.rxcui = s.rxcui
WHERE  s.atn = 'ATC' AND s.atv LIKE 'L04AB%'      -- TNF inhibitors
  AND  c.sab = 'RXNORM' AND c.tty IN ('IN','MIN');
```

Expand ingredient rxcui set to prescribable products:

```sql
WITH ingredients AS ( /* the seed rxcui list */ )
SELECT DISTINCT p.rxcui, p.str, p.tty
FROM   ingredients i
JOIN   rxnorm.rxnorm__rxnrel   r
       ON r.rxcui2 = i.rxcui
      AND r.rela IN ('ingredient_of','precise_ingredient_of','constitutes','has_tradename')
JOIN   rxnorm.rxnorm__rxnconso p
       ON p.rxcui = r.rxcui1
      AND p.sab = 'RXNORM' AND p.suppress = 'N'
      AND p.tty IN ('SCD','SBD','GPCK','BPCK');   -- add SCDC/SBDC for components
```

Attach NDC (only if your data is NDC-coded):

```sql
SELECT rxcui, atv AS ndc
FROM   rxnorm.rxnorm__rxnsat
WHERE  atn = 'NDC' AND rxcui IN ( /* valueset rxcui */ );
```

The final valueset SELECT should project the CSV columns:
`keyword` (your class label), `system` (the RxNorm URI), `code` = `rxcui`,
`display` = `str`.

## Presence check against real data (always)

`discovery__code_sources` (from the CORE `discovery` study,
`cumulus-library build --target discovery`) has columns
`table_name, column_name, code, display, system`. Which candidate codes actually
occur in this dataset's medications:

```sql
SELECT v.keyword, v.code, v.display,
       (d.code IS NOT NULL) AS present_in_data
FROM   example__rx_candidates v                      -- your candidate rxcui set
LEFT JOIN discovery__code_sources d
       ON d.code = v.code
      AND d.table_name IN ('medicationrequest','medicationdispense')
ORDER BY present_in_data;
```

If few/none are present, the dataset may be NDC- or locally-coded rather than RxNorm.
inspect `discovery__code_sources` `system`/`code` for the medication tables and switch
the valueset `system` (or add crosswalked NDC rows) accordingly.

## Cumulus valueset workflow (the heavy-duty path)

For a multi-source, agreement-checked, publishable valueset, a `config_type =
"valueset"` submanifest drives:

Config keys: `table_prefix`; `keyword_file` (one term per line); `vsac_stewards`
(VSAC valueset OIDs + steward id); `umls_stewards` (SAB + search terms);
`expansion_rules_file` (custom `REL`/`RELA` traversal rules. defaults provided).

Steps: seed (VSAC + keyword + UMLS string match) → expand (traverse `umls__MRREL` by
the configured REL/RELA) → rule/keyword filtering → integrate across stewards.

Outputs: `<prefix>__valuesets` (`rxcui, str, tty, sab, code, steward`) and
`<prefix>__combined_ruleset` (`rxcui1, rxcui2, tty1, tty2, rui, rel, rela, str1,
str2, keyword`). Flatten to an rx_ CSV:

```sql
SELECT DISTINCT 'anti_tnf' AS keyword,
       'http://www.nlm.nih.gov/research/umls/rxnorm' AS system,
       rxcui2 AS code, str2 AS display
FROM   example__combined_ruleset;
```

The `cumulus-library-opioid-valueset` is the exemplar: multiple steward seed sources
(ACEP, BioPortal, ECRI, CancerLinQ, VSAC), expanded by RxNorm-graph classifier rules
(`rxcui1 → rxcui2` via REL/RELA), keyword-matched, cross-source agreement scored
(Jaccard), then human-validated into the final valueset. Use the workflow when that
level of provenance and reproducibility is the goal; use this skill's direct rx_ CSV
when you want a fast, study-embedded valueset.

## Systems (canonical URIs)

- RxNorm: `http://www.nlm.nih.gov/research/umls/rxnorm`
- NDC: `http://hl7.org/fhir/sid/ndc`
- ATC: `http://www.whocc.no/atc`

## Verification checklist

- rxcui are current (RxNorm is monthly. check retired/remapped via RxNav or
  `rxnorm__rxncui` history).
- TTY set matches the intended breadth (generic-only vs +brand vs +packs).
- Combination products handled deliberately (`MIN`/`SCDC` decisions stated).
- Routes/dose forms filtered if the class is route-specific (via `DF`/`DFG`).
- Presence-checked against `discovery__code_sources` for
  medicationrequest/medicationdispense.
- Provenance recorded (which class axis, which relations, which stewards) for review.
