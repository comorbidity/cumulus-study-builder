"""Study-neutral clinical document-type selector for LLM chart review."""

from enum import StrEnum

from pydantic import BaseModel, Field

from cumulus_study_builder.llm.models.base import SpanAugmentedMention


class DocumentType(StrEnum):
    """Primary purpose of a clinical document."""

    PROCEDURE_NOTE = "PROCEDURE_NOTE"
    SURGICAL_OPERATION_NOTE = "SURGICAL_OPERATION_NOTE"
    PATHOLOGY_REPORT = "PATHOLOGY_REPORT"
    DIAGNOSTIC_IMAGING_STUDY = "DIAGNOSTIC_IMAGING_STUDY"
    HISTORY_AND_PHYSICAL = "HISTORY_AND_PHYSICAL"
    DISCHARGE_SUMMARY = "DISCHARGE_SUMMARY"
    CONSULT_NOTE = "CONSULT_NOTE"
    PROGRESS_NOTE = "PROGRESS_NOTE"
    NURSING_NOTE = "NURSING_NOTE"
    OTHER = "OTHER"


DOCUMENT_TYPE_DESCRIPTION = """
Classify the document into exactly one category according to its own primary purpose.
Use the title, author or service, encounter context, section headings, and body. Do not
classify a document from material that it merely quotes or summarizes. Apply these
definitions and tie-breaks:

PROCEDURE_NOTE: a report created for a completed invasive, non-operative procedure or
interventional treatment, including endoscopy, catheterization, bronchoscopy, bone
marrow aspiration, or interventional radiology. Exclude surgery, pathology, and
non-invasive diagnostic studies.

SURGICAL_OPERATION_NOTE: an operative or brief operative report created for a
completed surgery in an operative setting. A surgeon's authorship or the word
"surgical" alone is insufficient. A surgical progress note is PROGRESS_NOTE, and a
surgical pathology report is PATHOLOGY_REPORT.

PATHOLOGY_REPORT: a pathologist-authored interpretation of a biopsy or other specimen,
usually including a final diagnosis plus gross or microscopic findings. Prefer this
category over PROCEDURE_NOTE or SURGICAL_OPERATION_NOTE for surgical pathology and
biopsy-result reports.

DIAGNOSTIC_IMAGING_STUDY: a report interpreting a non-invasive imaging or diagnostic
study, including radiography, CT, MRI, ultrasound, PET, ECG/EKG, echocardiography,
pulmonary function testing, bone density, EEG, or EMG. Exclude laboratory results,
endoscopy and other invasive "-scopy" procedures, excision biopsy, and interventional
radiology.

HISTORY_AND_PHYSICAL: a clearly labeled H&P, history and physical, admission H&P,
preoperative H&P, or pre-procedure H&P documenting an initial evaluation. Do not infer
this type merely because another note contains history, examination, or assessment
sections. Exclude daily rounding and follow-up notes.

DISCHARGE_SUMMARY: a synopsis of a completed admission or outpatient episode that
summarizes the course, treatment, condition or disposition, and follow-up. A simple ED
discharge instruction sheet without a summary of care is OTHER.

CONSULT_NOTE: an initial consultation, referral, or requested specialist opinion,
including telemedicine or a second opinion. Distinguish it from an H&P and from ongoing
specialty follow-up, which is PROGRESS_NOTE.

PROGRESS_NOTE: an encounter-associated update on current clinical status, treatment,
or progress during hospitalization or outpatient follow-up. This includes specialty
follow-up, daily rounding, rehabilitation, nutrition, therapy, allied-health, surgical
progress, and nursing progress notes when their primary purpose is progress.

NURSING_NOTE: a generic nursing or nursing-admission note that does not meet a more
specific category. Use this only as a last resort when the title clearly identifies
nursing. Nursing progress notes are PROGRESS_NOTE, nursing H&Ps are
HISTORY_AND_PHYSICAL, and nursing discharge summaries are DISCHARGE_SUMMARY.

OTHER: a document that does not meet any category above, is administrative or
non-clinical, or lacks enough evidence for a more specific classification. Examples
include billing or authorization documents, patient instructions or education,
telephone encounters, refill requests, external laboratory reports, fax cover sheets,
claims, record requests, and other stand-alone external documents. Check every other
category before selecting OTHER.
"""


class DocumentTypeMention(SpanAugmentedMention):
    """Classify one clinical document before downstream extraction.

    Set ``has_mention`` to true when the title, headings, authoring context, or body
    provides document-specific classification evidence. Put the shortest verbatim
    title or section cues in ``spans``. Set ``has_mention`` to false, use ``OTHER``,
    and return an empty span list only when the document is empty, unreadable, or too
    ambiguous to classify more specifically.

    Document type is a routing feature, not a clinical phenotype. Study-specific
    extraction priority belongs in selector SQL rather than in this model.
    """

    document_type: DocumentType = Field(
        default=DocumentType.OTHER,
        description=DOCUMENT_TYPE_DESCRIPTION,
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description=(
            "Confidence in the document-type classification from 0.0 to 1.0. "
            "Use lower values when the title, authoring context, and body conflict "
            "or provide weak evidence."
        ),
    )


class DocumentTypeAnnotation(BaseModel):
    """Study-neutral document-type classification for one clinical document."""

    document_type: DocumentTypeMention
