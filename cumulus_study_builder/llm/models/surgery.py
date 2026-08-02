"""
Surgery extraction (generic example).

Extracts completed, study-qualifying surgical procedures from clinical text, with the
procedure category and, when stated, the date. A research user overrides `Surgery`
with the procedure categories their study defines.

Scoped to completed events (past or during the current encounter). Planned, discussed,
recommended, declined, and family-history surgeries are excluded at the extraction
layer.
"""
from enum import StrEnum
from pydantic import BaseModel, Field
from cumulus_study_builder.llm.models.base import SpanAugmentedMention, DatePrecision


###############################################################################
# Surgery category  (PLACEHOLDER — replace with your study's categories)
###############################################################################
class Surgery(StrEnum):
    TOTAL_RESECTION = "TOTAL_RESECTION"
    PARTIAL_RESECTION = "PARTIAL_RESECTION"
    BIOPSY_ONLY = "BIOPSY_ONLY"
    NON_QUALIFYING_SURGERY = "NON_QUALIFYING_SURGERY"
    NONE_OF_THE_ABOVE = "NONE_OF_THE_ABOVE"


class SurgeryMention(SpanAugmentedMention):
    """
    A completed surgical procedure documented in clinical text.

    Captures the procedure category and, when stated, the surgery date and the
    precision the text supports. Scoped to completed events; planned, recommended,
    declined, and family-history surgeries are excluded.
    """
    surgery: Surgery = Field(
        default=Surgery.NONE_OF_THE_ABOVE,
        description=(
            "Classify a completed, study-qualifying surgery (performed in the past or "
            "during the current encounter). Do not classify planned, recommended, "
            "possible, declined, or family-history surgeries. Replace these categories "
            "with the ones your study defines. "
            "TOTAL_RESECTION: complete removal of the affected organ or segment; "
            "PARTIAL_RESECTION: partial removal of the affected organ or segment; "
            "BIOPSY_ONLY: tissue sampling only, without resection; "
            "NON_QUALIFYING_SURGERY: a documented surgery that does not qualify for the "
            "study (e.g. an unrelated procedure); "
            "NONE_OF_THE_ABOVE: no qualifying surgery documented."
        ),
    )

    surgery_date: str | None = Field(
        None,
        description=(
            "Date the surgery was performed, in ISO YYYY-MM-DD (e.g. 2021-01-15). Null when "
            "no date is present. When only partial precision is available, emit the first "
            "date consistent with it (January 2021 -> 2021-01-01; 2021 -> 2021-01-01) and "
            "record the precision in surgery_date_precision."
        ),
    )

    surgery_date_precision: DatePrecision | None = Field(
        None,
        description=(
            "Precision supported by the source text for surgery_date. "
            "DAY: day, month, and year were explicitly stated; "
            "MONTH: month and year were explicitly stated; "
            "YEAR: only year was explicitly stated; "
            "null when surgery_date is null."
        ),
    )


###############################################################################
# Aggregated annotation
###############################################################################
class SurgeryAnnotation(BaseModel):
    """
    Patient-level surgery annotations from a single clinical note.

    Surgeries repeat, so this aggregates a list of mentions. Take care to avoid false
    positives — do not treat family-history or planned surgeries as completed events.
    """
    surgery_mentions: list[SurgeryMention] = Field(
        default_factory=list,
        description="Completed, study-qualifying surgeries the patient has undergone."
    )
