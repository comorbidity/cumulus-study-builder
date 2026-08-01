# RECONSTRUCTED (approximate) generic lab-panel base for chart review.
# Replace with the source `lab_base.py` on device sync if you want the exact
# base classes used by the source study's lab-panel annotations.
#
# Pattern: a single lab measurement mention (value + unit + interpretation),
# reused across panel-specific annotation models. Extend per your objective;
# keep enums parsimonious and decision-relevant.
from enum import StrEnum
from pydantic import BaseModel, Field
from cumulus_study_builder.llm.models.base import SpanAugmentedMention, DatePrecision

class LabInterpretation(StrEnum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    NONE_OF_THE_ABOVE = "NONE_OF_THE_ABOVE"

class LabValueMention(SpanAugmentedMention):
    """
    A single documented laboratory result for one analyte.

    Capture only patient-specific, documented results. Do not infer values, and
    do not extract reference ranges or family-history values.
    """
    value: float | None = Field(
        None,
        description="Numeric result value as documented, or null if not stated."
    )
    unit: str | None = Field(
        None,
        description="Units as documented (e.g. mg/dL), or null."
    )
    interpretation: LabInterpretation = Field(
        default=LabInterpretation.NONE_OF_THE_ABOVE,
        description=(
            "Documented interpretation. LOW / NORMAL / HIGH when the note states "
            "or clearly implies it; NONE_OF_THE_ABOVE when not documented."
        ),
    )
    result_date: str | None = Field(
        None,
        description=(
            "Result date in ISO YYYY-MM-DD, first-of-period when coarse; record the "
            "precision in result_date_precision. Null when no date is stated."
        ),
    )
    result_date_precision: DatePrecision | None = Field(
        None,
        description="Precision supported for result_date. DAY/MONTH/YEAR; null when result_date is null."
    )


class ExampleLabPanelAnnotation(BaseModel):
    """
    EXAMPLE lab-panel annotation. Rename per your panel and list the analytes
    your objective actually needs (each as its own LabValueMention field or a
    list[LabValueMention]).
    """
    lab_values: list[LabValueMention] = Field(
        default_factory=list,
        description="Documented lab results relevant to this panel."
    )
