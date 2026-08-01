# GENERIC treatment example (de-specialized: no disease-specific RxClass or
# medication lists). This shows the repeating-mention pattern: one annotation
# per medication context, aggregating status, phase, start date.
#
# To specialize: add an RxClass StrEnum with the drug classes your study needs,
# add response/adverse-event mentions if your objective requires them, and put
# the exact medication names/brands in the supporting spans. Keep every enum
# parsimonious — only values that drive a decision (inclusion/exclusion,
# treatment change, or outcome).
from enum import StrEnum
from pydantic import BaseModel, Field
from cumulus_study_builder.llm.models.base import SpanAugmentedMention, DatePrecision


class RxStatus(StrEnum):
    """
    Medication status, including intent (chart review is not always identical to
    FHIR MedicationRequest.status/intent).
    """
    INTENDED = "INTENDED"
    CANCELLED = "CANCELLED"
    ACTIVE = "ACTIVE"
    ON_HOLD = "ON_HOLD"
    COMPLETED = "COMPLETED"
    STOPPED = "STOPPED"
    NONE_OF_THE_ABOVE = "NONE_OF_THE_ABOVE"


class RxStatusMention(SpanAugmentedMention):
    rx_status: RxStatus = Field(
        RxStatus.NONE_OF_THE_ABOVE,
        description=(
            "Status of this medication. Choose one: "
            "INTENDED: planned, ordered, or prescribed but not yet started; "
            "CANCELLED: order withdrawn before any doses; "
            "ACTIVE: currently prescribed, currently taking, or ongoing; "
            "ON_HOLD: temporarily paused, suspended, or interrupted; "
            "COMPLETED: finite course finished as intended; "
            "STOPPED: permanently discontinued; "
            "NONE_OF_THE_ABOVE: status not mentioned, unclear, or not captured by these options."
        ),
    )


class RxStartDateMention(SpanAugmentedMention):
    rx_start_date: str | None = Field(
        None,
        description=(
            "Date of the first dose of this medication, ISO YYYY-MM-DD. Always emit a "
            "full YYYY-MM-DD; first-of-period when coarse, recording precision in "
            "rx_start_date_precision."
        ),
    )
    rx_start_date_precision: DatePrecision | None = Field(
        None,
        description="Precision supported for rx_start_date. DAY/MONTH/YEAR; null when rx_start_date is null."
    )


class RxAnnotation(BaseModel):
    """
    A single medication context. Put the exact medication name / brand /
    abbreviation in the supporting spans. All nested mentions should refer to the
    same medication context.
    """
    rx_status: RxStatusMention
    rx_start_date: RxStartDateMention


class ExampleTreatmentAnnotation(BaseModel):
    """
    EXAMPLE treatment annotation. Create one RxAnnotation per medication context.
    Rename and extend per your study objective.
    """
    rx_annotations: list[RxAnnotation] = Field(
        default_factory=list,
        description=(
            "Medication-level annotations mentioned in the note. Include current, "
            "historical, planned, stopped, held, or completed medications. Create a "
            "separate RxAnnotation per medication."
        ),
    )
