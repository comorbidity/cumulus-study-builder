"""
Generic lab-panel base for chart review.

Pattern: a single laboratory measurement mention (numeric value + unit +
interpretation + result date). Subclass `LabBaseMention` once per analyte to build
a panel (see lab_panel_cbc.py / lab_panel_cmp.py / lab_panel_iron.py) — the subclass
name and docstring identify the analyte, and every analyte inherits the fields below.

Keep enums parsimonious and decision-relevant; a research user overrides the analytes
and interpretation to fit their study.
"""
from enum import StrEnum
from pydantic import BaseModel, Field
from cumulus_study_builder.llm.models.base import SpanAugmentedMention, DatePrecision


class LabInterpretation(StrEnum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    NONE_OF_THE_ABOVE = "NONE_OF_THE_ABOVE"


class LabBaseMention(SpanAugmentedMention):
    """
    A single documented laboratory result for one analyte.

    Shared base for lab-panel extraction. Subclass once per analyte; the subclass name
    and docstring name the analyte, and each analyte inherits value_numeric, unit,
    interpretation, and result date from here.

    Capture only patient-specific, documented results. Do not infer values, and do not
    extract reference ranges or family-history values.
    """
    value_numeric: float | None = Field(
        None,
        description="Numeric result value exactly as documented, or null if not stated."
    )
    unit: str | None = Field(
        None,
        description="Units exactly as documented (e.g. mg/dL, g/dL, x10^3/uL), or null."
    )
    interpretation: LabInterpretation = Field(
        default=LabInterpretation.NONE_OF_THE_ABOVE,
        description=(
            "Documented interpretation of the result. "
            "LOW / NORMAL / HIGH when the note states or clearly flags it; "
            "NONE_OF_THE_ABOVE when no interpretation is documented."
        ),
    )
    result_date: str | None = Field(
        None,
        description=(
            "Result date in ISO YYYY-MM-DD. Always emit a full date; when only month or "
            "year precision is supported, use the first date consistent with it "
            "(January 2021 -> 2021-01-01) and record the precision in result_date_precision. "
            "Null when no date is stated."
        ),
    )
    result_date_precision: DatePrecision | None = Field(
        None,
        description=(
            "Precision supported by the text for result_date. DAY / MONTH / YEAR; "
            "null when result_date is null."
        ),
    )


class ExampleLabPanelAnnotation(BaseModel):
    """
    Minimal example lab panel — a flat list of results.

    The simplest panel shape. For the named-analyte pattern (one field per analyte,
    each an analyte-specific subclass), see lab_panel_cbc.py. Replace this with the
    analytes your objective needs.
    """
    lab_values: list[LabBaseMention] = Field(
        default_factory=list,
        description="Documented laboratory results relevant to this panel."
    )
