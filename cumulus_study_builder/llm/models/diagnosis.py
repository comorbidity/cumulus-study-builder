"""
Disease diagnosis extraction (generic example).

Extracts, from a single clinical note, the patient's disease subtype, age at first
diagnosis, first-diagnosis date, a confirmatory ("gold") diagnostic date, and current
activity/severity. A research user overrides `DiseaseType` (and the subtype and
severity vocabularies) with the categories their study defines.

Do not extract family history, negated disease, rule-out, or
suspected/probable/working diagnoses at the extraction layer.
"""
from enum import StrEnum
from pydantic import BaseModel, Field
from cumulus_study_builder.llm.models.base import SpanAugmentedMention, DatePrecision


###############################################################################
# Disease subtype  (PLACEHOLDER — replace TYPE_* with your study's subtypes)
###############################################################################
class DiseaseType(StrEnum):
    TYPE_I = "TYPE_I"
    TYPE_IIA = "TYPE_IIA"
    TYPE_IIB = "TYPE_IIB"
    NONE_OF_THE_ABOVE = "NONE_OF_THE_ABOVE"


class DiseaseTypeMention(SpanAugmentedMention):
    """
    Patient's documented disease subtype.

    If multiple subtypes appear, classify by the most recently affirmed diagnosis in
    this note. Capture explicit diagnostic statements only; do not infer subtype from
    symptoms, medications, imaging, or pathology unless the note states the diagnosis
    or subtype. Do not extract negated, rule-out, suspected/probable/working, or
    family-history diagnoses.
    """
    disease_type: DiseaseType = Field(
        default=DiseaseType.NONE_OF_THE_ABOVE,
        description=(
            "Documented disease subtype using only evidence from this note. "
            "Choose exactly one value. "
            "TYPE_I: concise definition for disease subtype I; "
            "TYPE_IIA: concise definition for disease subtype IIA; "
            "TYPE_IIB: concise definition for disease subtype IIB; "
            "NONE_OF_THE_ABOVE: no patient-level disease diagnosis is documented in this note."
        ),
    )


###############################################################################
# Age at diagnosis
###############################################################################
class AgeAtDiagnosisMention(SpanAugmentedMention):
    """
    Patient's age at their initial disease diagnosis, in completed months.

    Extract only when the note explicitly states the age at diagnosis. Do not derive
    age from a diagnosis date combined with a date of birth. Do not extract from
    family-history, negated, rule-out, or suspected diagnoses.
    """
    age_at_diagnosis_months: int | None = Field(
        default=None,
        ge=0,
        le=1500,  # generous ceiling in months; tighten for your population
        description=(
            "Patient's age in completed months at first diagnosis. Extract only when the "
            "note explicitly states the age at diagnosis (e.g. 'diagnosed at 18 months', "
            "'diagnosed at age 4'). For ages stated in years, use the floor in months "
            "(age 4 -> 48)."
        ),
    )


###############################################################################
# First diagnosis date — any evidence source
###############################################################################
class DiagnosisDateMention(SpanAugmentedMention):
    """
    Date the patient was first diagnosed with the disease (any subtype, any source).

    If multiple diagnoses are described (e.g. original diagnosis and later
    reclassification), use the earliest. Do not extract family-history, negated,
    rule-out, or suspected diagnoses.
    """
    diagnosis_date: str | None = Field(
        None,
        description=(
            "Earliest date the disease is affirmatively documented as a diagnosis, in ISO "
            "YYYY-MM-DD (e.g. 2021-01-15). Always emit a full YYYY-MM-DD. If only month or "
            "year precision is supported, use the first date consistent with it "
            "(January 2021 -> 2021-01-01; 2021 -> 2021-01-01) and record the precision in "
            "diagnosis_date_precision."
        ),
    )

    diagnosis_date_precision: DatePrecision | None = Field(
        None,
        description=(
            "Precision supported by the source text for diagnosis_date. "
            "DAY: day, month, and year were explicitly stated; "
            "MONTH: month and year were explicitly stated; "
            "YEAR: only year was explicitly stated; "
            "null when diagnosis_date is null."
        ),
    )


###############################################################################
# Confirmatory ("gold") diagnostic date
###############################################################################
class DiagnosisDateGoldMention(SpanAugmentedMention):
    """
    Date of the confirmatory ("gold standard") diagnostic procedure or study that first
    established the diagnosis — for example an endoscopy, biopsy, or imaging study,
    depending on the disease.

    If multiple confirmatory studies are described, use the earliest one that
    established the diagnosis, and prefer the procedure date over a later pathology
    confirmation date. Do not extract from surveillance procedures that did not
    establish the diagnosis, nor from family-history, negated, rule-out, or suspected
    diagnoses.
    """
    diagnosis_date_gold: str | None = Field(
        None,
        description=(
            "Date of the confirmatory diagnostic procedure or study that first established "
            "the diagnosis, in ISO YYYY-MM-DD (e.g. 2021-01-15). Always emit a full "
            "YYYY-MM-DD. If only month or year precision is supported, use the first date "
            "consistent with it (January 2021 -> 2021-01-01; 2021 -> 2021-01-01) and record "
            "the precision in diagnosis_date_gold_precision."
        ),
    )

    diagnosis_date_gold_precision: DatePrecision | None = Field(
        None,
        description=(
            "Precision supported by the source text for diagnosis_date_gold. "
            "DAY: day, month, and year were explicitly stated; "
            "MONTH: month and year were explicitly stated; "
            "YEAR: only year was explicitly stated; "
            "null when diagnosis_date_gold is null."
        ),
    )


###############################################################################
# Disease severity / activity
###############################################################################
class DiseaseSeverity(StrEnum):
    """
    Current documented disease severity. Range phrases are intentionally included
    because extraction is usually better when enum options match note language.
    """
    MILD = "MILD"
    MILD_TO_MODERATE = "MILD_TO_MODERATE"
    MODERATE = "MODERATE"
    MODERATE_TO_SEVERE = "MODERATE_TO_SEVERE"
    SEVERE = "SEVERE"
    NONE_OF_THE_ABOVE = "NONE_OF_THE_ABOVE"


class DiseaseActivity(StrEnum):
    """Current documented disease activity."""
    REMISSION = "REMISSION"
    ACTIVE = "ACTIVE"
    NONE_OF_THE_ABOVE = "NONE_OF_THE_ABOVE"


class DiseaseActivityAndSeverityMention(SpanAugmentedMention):
    """
    Current documented disease activity and severity.

    Examples:
    * "in remission" -> activity=REMISSION, severity=NONE_OF_THE_ABOVE
    * "active disease" -> activity=ACTIVE, severity=NONE_OF_THE_ABOVE
    * "mild disease" -> activity=ACTIVE, severity=MILD
    * "moderate to severe disease" -> activity=ACTIVE, severity=MODERATE_TO_SEVERE

    If a severity is negated (e.g. "no severe disease"), do not assign it. If multiple
    severities appear for different sites, use the highest. Do not infer severity from
    medication intensity, and do not use a historical severity if the patient is now in
    remission. Do not extract family-history, negated, rule-out, or suspected disease.
    """
    disease_activity: DiseaseActivity = Field(
        default=DiseaseActivity.NONE_OF_THE_ABOVE,
        description=(
            "Current documented disease activity. "
            "ACTIVE: current active disease, active inflammation, active flare, or active "
            "symptoms documented and attributed to the disease; "
            "REMISSION: remission, quiescent, inactive, or asymptomatic disease documented "
            "as the current state; "
            "NONE_OF_THE_ABOVE: current activity is not documented."
        ),
    )

    disease_severity: DiseaseSeverity = Field(
        default=DiseaseSeverity.NONE_OF_THE_ABOVE,
        description=(
            "Current documented disease severity. Use the value that best matches the "
            "clinician's wording. "
            "MILD / MILD_TO_MODERATE / MODERATE / MODERATE_TO_SEVERE / SEVERE for those "
            "phrases; "
            "NONE_OF_THE_ABOVE: severity is not documented, or only activity is documented "
            "without a severity grade."
        ),
    )


###############################################################################
# Aggregated annotation
###############################################################################
class DiseaseDiagnosisAnnotation(BaseModel):
    """
    Patient-level disease-diagnosis annotations from a single clinical note: subtype,
    age at first diagnosis, first-diagnosis date, confirmatory diagnostic date, and
    current activity/severity.

    Do not extract family-history, negated, rule-out, or suspected diagnoses.
    """
    disease_type: DiseaseTypeMention
    age_at_diagnosis: AgeAtDiagnosisMention
    diagnosis_date: DiagnosisDateMention
    diagnosis_date_gold: DiagnosisDateGoldMention
    activity_and_severity: DiseaseActivityAndSeverityMention
