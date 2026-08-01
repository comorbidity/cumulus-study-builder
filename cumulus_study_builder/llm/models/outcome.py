from enum import StrEnum
from pydantic import BaseModel, Field
from cumulus_study_builder.llm.models.base import SpanAugmentedMention,DatePrecision

###############################################################################
# Surgery
#
# Notably, the IBD surgeries stratify by frequency in each IBD subtype.
# Surgery types exclusive to CD type imply IBD reclassification to CD.
# Surgery types suggestive of UC type suggest IBD reclassification to UC.
#
# CD = Crohn's disease:
# ----------------------
# BOWEL_RESECTION (incudes Dr. Collen recommended "ileocecectomy").
# STRICTUROPLASTY
# PERIANAL_CROHNS_SURGERY

# UC = Ulcerative Colitis:
# ------------------------
# COLECTOMY (very rare in CD)

# All IBD types:
# --------------
# OSTOMY_OR_FECAL_DIVERSION
###############################################################################
class Surgery(StrEnum):
    TOTAL_RESECTION = "TOTAL_RESECTION"
    PARTIAL_RESECTION = "PARTIAL_RESECTION"
    BIOPSY_ONLY = "BIOPSY_ONLY"
    NON_QUALIFYING_SURGERY = "NON_QUALIFYING_SURGERY"
    NONE_OF_THE_ABOVE = "NONE_OF_THE_ABOVE"

class SurgeryMention(SpanAugmentedMention):
    """Extraction of a completed IBD-related surgical procedure from clinical text.

    Captures the procedure category and, when stated, the date of the surgery
    along with the precision actually supported by the source text. Scoped to
    completed events (past or during the current encounter); planned, discussed,
    declined, and family-history surgeries are excluded at the extraction layer.

    Attributes:
        surgery: The category of completed IBD-related surgery referenced in the text.
        surgery_date: ISO-format date the surgery was performed, or null when no
            date information is present.
        surgery_date_precision: The precision actually supported by the source
            text for surgery_date.
    """
    surgery: Surgery = Field(
        default=Surgery.NONE_OF_THE_ABOVE,
        description=(
            "Classify a completed IBD-related surgery — performed in the past or during the "
            "current encounter. Do not classify planned, recommended, possible, "
            "denied, or family-history surgeries. "
            "COLECTOMY: colectomy, proctocolectomy, or IPAA / J-pouch at any stage. "
            "BOWEL_RESECTION: ileocecectomy, ileocolic resection, or small bowel resection. "
            "STRICTUROPLASTY: strictureplasty (any technique). "
            "OSTOMY_OR_FECAL_DIVERSION: diverting ostomy, new ileostomy, colostomy, fecal diversion, or ostomy revision. "
            "PERIANAL_CROHNS_SURGERY: seton, perianal fistula surgery, or perianal abscess drainage in Crohn's disease. "
            "NON_QUALIFYING_SURGERY: endoscopy, biopsy, ostomy reversal, or "
            "unrelated surgery (e.g., appendectomy, cholecystectomy). "
            "NONE_OF_THE_ABOVE: no completed IBD-related surgery documented."
        ),
    )

    surgery_date: str | None = Field(
        None,
        description=(
            "Date the surgery was performed, in ISO YYYY-MM-DD format (e.g., 2021-01-15). "
            "Emit null when no date information is present in the text. "
            "When only partial precision is available, emit the first date consistent "
            "with the stated precision (January 2021 -> 2021-01-01; 2021 -> 2021-01-01) "
            "and record the actual precision in surgery_date_precision."
        ),
    )

    surgery_date_precision: DatePrecision | None = Field(
        None,
        description=(
            "Precision actually supported by the source text for surgery_date. "
            "DAY: day, month, and year were explicitly stated; "
            "MONTH: month and year were explicitly stated; "
            "YEAR: only year was explicitly stated; "
            "null: surgery_date is null or no date information is available."
        ),
    )

###############################################################################
# Aggregated Annotation and Mention Classes
#
# This is the top-level structure for the pydantic models used for IBD surgery.
###############################################################################

class IbdSurgeryAnnotation(BaseModel):
    """
    An object-model for annotations of inflammatory bowel disorder observations
    found in a patient's chart, related to IBD surgical events.
    Take care to avoid false positives, like confusing information that only
    appears in family history for patient history. Annotations should indicate
    the relevant details of the finding, as well as some additional evidence
    metadata to validate findings post-hoc.
    """
    surgery_mentions: list[SurgeryMention] = Field(
        default_factory=list,
        description='A list of mentions of which IBD related surgeries the patient has undergone.'
    )
