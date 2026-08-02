---
name: chart-review
description: >-
  Author Pydantic chart-review models for the cumulus-study-builder LLM/NLP layer,
  including first-pass document-type and topic-relevance selectors that route notes
  to downstream extraction tasks. Use when defining or editing a clinical-note
  phenotype for diagnosis, treatment, labs, severity, findings, document type, or
  topic relevance. Models use StrEnum choices, SpanAugmentedMention evidence, precise
  docstrings and Field descriptions, and a top-level Annotation. If criteria are
  missing, elicit the research objective and keep only decision-relevant values.
  Author the model; create_*.py generates schemas, summaries, flattening SQL, and NLP
  wiring.
---

# chart-review — LLM clinical-note extraction models

Author a **Pydantic chart-review model**: the strongly-typed definition of what an
LLM should extract from a clinical note for a computable phenotype that needs the
free text. The model lives in `llm/models/<name>.py`. Its enums, class docstrings,
and `Field(description=...)` strings ARE the chart-review instructions handed to the
model at extraction time. Replace `example` below with your study prefix.

For large note sets, use two passes: first classify document type and topic relevance;
then run diagnosis, treatment, laboratory, outcome, or other phenotype extraction only
on selected notes. Selectors reduce cost and noise. They are routing evidence, not
phenotype truth.

Scope: this skill authors the **Pydantic model only**. The JSON schema, the flatten
builder + jinja, the summary, and the nlp task wiring are generated from the model by
the `create_*.py` scripts — this skill instructs those steps but does not write them
(see "Downstream"). The starter ships worked, deliberately generic models under
`llm/models/` — use them as templates and override the vocabularies for your study:
`treatment.py` (status + start-date medication), `lab_base.py` (the single-lab-value
base reused by panels), `diagnosis.py` (a placeholder disease-type enum, age at
diagnosis, first-diagnosis and gold-standard-confirmed "gold" dates with
`DatePrecision`, and a combined activity + severity Mention), the lab panels
`lab_panel_cbc.py` / `lab_panel_cmp.py` / `lab_panel_iron.py` (the per-analyte panel
pattern), `surgery.py` (a placeholder completed-surgery category + date), and two
note-routing classifiers — `document_type.py` (the fixed, study-neutral clinical-note
taxonomy) and `document_topic.py` (a customizable per-topic relevance gate deciding
which extraction models a note is worth running) — plus `base.py`.

Notes come, by default, from **FHIR DiagnosticReport and DocumentReference**, sampled
by casedef temporality (`pre` / `peri` / `peri_post` / `post` relative to the first
case-defining encounter) via `tools/sample.py`. You are designing what to pull out of
those notes.

## Start from the OBJECTIVE

If the researcher already has explicit criteria, encode them. If they don't, do not
guess — **elicit the objective first**. Ask what decision the chart review serves,
because that determines which enum values are worth extracting:

- What phenotype or question is this for? What will the extracted value be used to
  decide?
- Is this for a **CDS clinical pathway** (the value changes a care recommendation), a
  **clinical trial** (the value maps to inclusion/exclusion, a treatment decision, or
  an outcome measure), or a descriptive cohort characteristic?
- What are the mutually-exclusive answers a clinician would actually record?
- What must be excluded (family history, negation, rule-out, suspected, historical)?

Only after the objective is clear do you design the enums.

## Enum design — parsimony is the point

This is the heart of the skill. An enum value must earn its place by **driving a
decision**. Include a value only if a clinician would actually choose it and it
changes something downstream — a CDS branch, a trial inclusion/exclusion criterion, a
treatment decision, or an outcome measurement. If a detail is clinically interesting
but does not change decision-making, **leave it out**. A shorter, decision-relevant
enum extracts more reliably and is easier to validate than a long taxonomy.

Rules:

- **Discrete and coded.** Enum values are fixed categories, not free text. Plain
  `StrEnum` written `KEY = "VALUE"` (key equals value), e.g. `ACTIVE = "ACTIVE"`.
- **Always include `NONE_OF_THE_ABOVE`** in clinical-concept enums as the
  default/fallback so the model has a clean "not documented / not applicable" answer.
  The fixed document-type taxonomy is the exception: its fallback is `OTHER`.
- **Mutually exclusive, collectively sufficient** for the decision. Prefer the
  smallest set that covers the choices the objective needs.
- **Match clinician language** when it improves extraction — e.g. severity as
  `MILD`, `MILD_TO_MODERATE`, `MODERATE`, `MODERATE_TO_SEVERE`, `SEVERE` because
  notes use those phrases (a documented, deliberate exception to strict minimalism).
- **Trial framing:** if the objective is a trial, each enum value should correspond
  to an inclusion/exclusion criterion, a treatment decision, or an outcome; drop
  categories that serve none of these.

## Anatomy of a model

Build on `llm/models/base.py`:

- `SpanAugmentedMention(BaseModel)` — carries `has_mention: bool` and
  `spans: list[str]` (verbatim supporting text) for auditability. Every Mention class
  subclasses it.
- `DatePrecision(StrEnum)` — `DAY` / `MONTH` / `YEAR`, paired with a `str | None` ISO
  date field (emit a full `YYYY-MM-DD`, first-of-period when coarse, and record the
  precision).

A model file has three layers:

1. **Enums** — one `StrEnum` per coded concept (plain KEY=VALUE, `NONE_OF_THE_ABOVE`
   last). A short docstring may explain the intent.
2. **Mention classes** — subclass `SpanAugmentedMention`. The **class docstring**
   states scope and exclusions (negation, family history, rule-out, historical), and
   each `Field(..., description="...")` carries the per-value extraction criteria in
   plain language, one clause per enum value (`VALUE: when to choose it; ...`).
   Include worked examples and tie-breaks (e.g. "use the highest severity", "use the
   earliest date", strongest-evidence ordering) in the docstring.
3. **Top-level Annotation** — a `BaseModel` named `Example<Name>Annotation` that
   aggregates the mentions. Use a single Mention field for a patient-level concept
   (one diagnosis per note) and a `list[...] = Field(default_factory=list, ...)` when
   the concept repeats (one per medication, one per finding).

Minimal skeleton:

```python
from enum import StrEnum
from pydantic import BaseModel, Field
from cumulus_study_builder.llm.models.base import SpanAugmentedMention

class ThingType(StrEnum):
    OPTION_A = "OPTION_A"
    OPTION_B = "OPTION_B"
    NONE_OF_THE_ABOVE = "NONE_OF_THE_ABOVE"

class ThingMention(SpanAugmentedMention):
    """One decision-relevant concept. State scope and exclusions here
    (no family history, negation, rule-out, or historical)."""
    thing: ThingType = Field(
        default=ThingType.NONE_OF_THE_ABOVE,
        description=(
            "Choose one. "
            "OPTION_A: <when to choose A>; "
            "OPTION_B: <when to choose B>; "
            "NONE_OF_THE_ABOVE: not documented or not captured by these options."
        ),
    )

class ExampleThingAnnotation(BaseModel):
    """Patient-level extraction for <objective>."""
    thing: ThingMention
```

See `llm/models/treatment.py`, `lab_base.py`, and `diagnosis.py` for full, well-formed
examples (single vs list aggregation, dates with precision, status enums, and two
related enums in one Mention — `diagnosis.py`'s `DiseaseActivityAndSeverityMention`
carries both activity and severity).

**Panel pattern (many analytes).** For a lab panel, define one shared base Mention in
`lab_base.py` (the numeric value + unit + interpretation + date), then subclass it once
per analyte with just a docstring naming that analyte, and aggregate them as fields of
a single panel Annotation. See `lab_panel_cbc.py` / `cmp` / `iron`. Keep the base class
name and its numeric-value field name identical to what those subclasses inherit — a
mismatch (e.g. a base named `LabValueMention` while panels subclass `LabBaseMention`)
makes every panel fail to import.

## Note-routing selectors

`document_type.py` and `document_topic.py` run *upstream* of phenotype extraction.

**Document type.** Keep the document-type taxonomy fixed unless the annotation
guideline changes: `PROCEDURE_NOTE`, `SURGICAL_OPERATION_NOTE`, `PATHOLOGY_REPORT`,
`DIAGNOSTIC_IMAGING_STUDY`, `HISTORY_AND_PHYSICAL`, `DISCHARGE_SUMMARY`,
`CONSULT_NOTE`, `PROGRESS_NOTE`, `NURSING_NOTE`, and `OTHER`. Classify the document's
own primary purpose, not material copied into it. Important tie-breaks are encoded in
the model: surgical pathology is pathology; surgical and nursing progress notes are
progress; nursing is a last-resort category; endoscopy and interventional radiology
are invasive procedure notes; non-invasive studies are diagnostic imaging. Do not put
disease specialties, care settings, or yield tiers in the Pydantic model. Each
downstream task defines its own high-recall document-type allowlist in SQL.

Preserve `result.document_type.document_type` so the first selector flattens to one
`document_type` column per note.

**Topic relevance.** Keep the shared `EXPLICIT` / `IMPLICIT` /
`NONE_OF_THE_ABOVE` contract. Customize the top-level topic fields so each maps to one
downstream extraction task. For every topic, write study-specific explicit criteria
and concrete implicit criteria; `IMPLICIT` must not mean merely "seems related."
State the minimum evidence or combination of findings required. Keep these invariants:

- `has_mention=true` exactly for `EXPLICIT` or `IMPLICIT`.
- Relevant topics cite the shortest verbatim spans; `NONE_OF_THE_ABOVE` uses an empty
  span list and null reasoning.
- Do not count negation, rule-out, hypothetical, or family-history evidence unless the
  topic definition explicitly asks for it.
- Do not use a computed `is_relevant` threshold in the model. Selection policy belongs
  in SQL and can vary by topic and validation results.

The starter uses fixed topic fields because they flatten to easy-to-read
`<topic>_relevance` and `<topic>_confidence` column pairs, matching the selector SQL
pattern. For a study with a large or frequently changing topic registry, a
`topics: list[TopicRelevanceMention]` plus a tall note/topic table is a valid
alternative.

## Naming

- File: `llm/models/<name>.py`. Enums `StrEnum`; mentions `<Concept>Mention`;
  top-level `Example<Name>Annotation` (or your study's capitalization).
- Reuse `NONE_OF_THE_ABOVE` for clinical concepts, the `DatePrecision` pattern, and
  the exclusion language from the existing models so extraction behaves consistently
  across tasks. Preserve `OTHER` as the document-type fallback.
- **Import from this package.** every model imports its base from
  `cumulus_study_builder.llm.models.base` (panels from `...lab_base`). when you copy a
  model in from another study, fix the import to this package — a leftover
  `cumulus_library_ibd_cds` import will not load here.
- **Descriptions must name THIS model's fields.** the `Field(description=...)` text is
  the prompt. when copying a model, update every description that references a sibling
  field so it names the field that actually exists here; stale names (e.g. a leftover
  `ibd_diagnosis_date`) mislead the extractor.

## Downstream (instruct only — do not run)

After authoring `llm/models/<name>.py`, tell the researcher the steps to wire it in
(each just registers the new `Annotation`):

1. **Schema** — import the Annotation in `llm/create_schema.py`, add
   `create(Example<Name>Annotation, 'example-<name>-annotation.json')` to `create_all()`,
   and run it → `llm/schemas/example-<name>-annotation.json` (the LLM extraction
   contract).
2. **Summary** — import it in `llm/create_model_summary.py` and run it →
   `llm/summaries/<name>_summary.txt` (human-readable).
3. **Flatten to a table** — add `llm/builder/example_<name>_wide.py` (a
   `BaseTableBuilder` subclass listing the flat columns), a
   `llm/template/example__llm_<name>_wide.sql.jinja` that `CROSS JOIN UNNEST`es the
   result, export it in `llm/builder/__init__.py`, add it to
   `create_wide_and_highlight_sql_examples.py`, and run that → the athena wide SQL.
4. **NLP wiring** — add a `[tables.<name>]` entry in an `nlp_clinical_tasks.toml`
   (`response_schema = "llm/schemas/example-<name>-annotation.json"`, a
   `select_by_table`), and list the builder in `nlp_clinical_tasks_wide.toml`. (The
   starter ships the NLP tomls commented out in `manifest.toml`; enable them when you
   run extraction.)

The NLP step itself (a configured model) runs the extraction from the sampled notes
into `example__nlp_<name>_*`, which the wide SQL flattens. The shared `system_prompt`
injects the JSON schema (`%JSON-SCHEMA%`) and note (`%CLINICAL-NOTE%`) and enforces
patient-specific, verbatim-span, schema-conformant output — so the model's
descriptions are effectively the prompt.

### Wire selectors into task routing

Register document type and topic relevance as two first-pass NLP tables in the same
task TOML, each with its own response schema. Flatten them before building extraction
task tables:

- Document type: one row per note with `note_ref`, `encounter_ref`, `subject_ref`,
  `document_type`, and `confidence`.
- Topic relevance: one row per note with `<topic>_relevance` and
  `<topic>_confidence` pairs, or one row per note/topic for the optional tall shape.

Build each extraction selector from both signals. Select a note when the task's topic
is `EXPLICIT` or `IMPLICIT`, **or** when its document type is in that task's deliberate
high-recall allowlist. Join on `note_ref` and validate `subject_ref`; join case
definition or study encounter only for cohort scope and metadata. Point the downstream
task's `select_by_table` at this selector.

Choose one canonical row per note and selector version/model before joining so repeat
runs do not multiply rows. Carry `task_version`, `origin`, and `system_fingerprint` for
reproducibility. Optionally create a bounded false-negative review sample with a left
anti-join from all classified notes to selected notes.

## Header / docstring style

The extraction quality lives in the docstrings and `Field` descriptions. Write them
precisely and imperatively; separate sentences with periods, not semicolons, in prose
(house style), though the `VALUE: clause; VALUE: clause` list form inside a
`description` is the established pattern and is fine.

## Worked example

Objective: "For a trial, know whether the note documents a treatment-limiting adverse
event that would drive stopping a therapy." → the decision is stop/continue, so the
enum is the adverse-event categories that change therapy, each mapping to a
stop/switch decision, plus `NONE_OF_THE_ABOVE` — not a full toxicity ontology. Author
the Mention with per-value criteria and exclusions in the description, aggregate as a
`list[...]`, then print the downstream wiring steps.
