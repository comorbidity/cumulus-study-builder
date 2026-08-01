from enum import StrEnum
from pydantic import BaseModel, Field
from cumulus_study_builder.llm.models.base import SpanAugmentedMention, DatePrecision

###############################################################################
# Disease SubType
###############################################################################
class DiseaseType(StrEnum):
    TYPE_I = "TYPE_I"
    TYPE_IIA = "TYPE_IIA"
    TYPE_IIB = "TYPE_IIB"
    NONE_OF_THE_ABOVE = "NONE_OF_THE_ABOVE"

class DiseaseTypeMention(SpanAugmentedMention):
    """
    Patient's documented Disease subtype.

    If multiple IBD subtypes appear, classify based on the most recently affirmed IBD diagnosis in this note.

    Captures explicit diagnostic statements only; do not infer subtype from
    symptoms, medication use, imaging findings, endoscopy findings, or pathology
    findings unless the note states the diagnosis or subtype.

    Do not extract negated IBD, rule-out IBD, suspected/probable/working-diagnosis IBD, or non-IBD colitis.
    Do not extract a family history of IBD.
    """
    ibd_type: DiseaseType = Field(
        default=DiseaseType.NONE_OF_THE_ABOVE,
        description=(
            "Documented disease subtype using only evidence from this note. "
            "Choose exactly one value. "
            "TYPE_I: concise definition for disease subtype I; "
            "TYPE_IIA: concise definition for disease subtype IIA; "
            "TYPE_IIB: concise definition for disease subtype IIB; "
            "NONE_OF_THE_ABOVE: no patient-level disease diagnosis is documented in this note. "),
    )

###############################################################################
# Age of IBD diagnosis
###############################################################################
class AgeAtDiagnosisMention(SpanAugmentedMention):
    """
    Patient's age at the time of their initial disease diagnosis, in completed months.

    Do not derive age from documented diagnosis dates combined with date of birth.

    Do not extract IBD family history, disease negated, IBD rule-out, or IBD suspected/probable/working-diagnosis.
    """
    age_at_diagnosis_months: int | None = Field(
        default=None,
        ge=0,
        le=300, #18 years old + 7 years followup conservative ceiling for pediatric hospital
        description=("Patient's age in completed months at the time of their first IBD diagnosis. "
                     "Extract only when the note explicitly states the patient's age at IBD diagnosis "
                     "(e.g., 'diagnosed at 18 months', 'IBD diagnosed at age 4'). "
                     "For ages stated in years, use the floor in months (age 4 -> 48).")
    )

###############################################################################
# First IBD Diagnosis Date - Any Evidence Source
###############################################################################
class DiagnosisDateMention(SpanAugmentedMention):
    """
    Date on which the patient was first diagnosed with DiseaseType (any subtype).

    If multiple diagnoses are described (e.g., original diagnosis and later reclassification), use the earliest.
    Extract documented IBD diagnoses in any evidence source, including endoscopic procedures.

    Do not extract family history, negated, rule-out, or suspected/probable/working-diagnosis.
    """
    diagnosis_date: str | None = Field(
        None,
        description=("Earliest date on which disease is affirmatively documented as a diagnosis, "
                     "in ISO YYYY-MM-DD format (e.g. 2021-01-15). Always emit a full YYYY-MM-DD value. "
                     "If only month or year precision is supported by the text, "
                     "use the first possible date consistent with it (January 2021 -> 2021-01-01; "
                     "2021 -> 2021-01-01) and record the actual precision in diagnosis_date_precision.")
    )

    diagnosis_date_precision: DatePrecision | None = Field(
        None,
        description=("Precision actually supported by the source text for ibd_diagnosis_date. "
                     "DAY: day, month, and year were explicitly stated; "
                     "MONTH: month and year were explicitly stated; "
                     "YEAR: only year was explicitly stated; "
                     "Use null when ibd_diagnosis_date is null.")
    )

###############################################################################
# Example: IBD Diagnosis Date *CONFIRMED ON ENDOSCOPY*
###############################################################################
class DiagnosisDateGoldMention(SpanAugmentedMention):
    """
    Date of the endoscopic procedure that first established the patient's IBD diagnosis.

    If multiple endoscopic procedures are described, use the earliest one that established the IBD diagnosis.
    Prefer the procedure date over the pathology confirmation date.

    Do not extract from surveillance endoscopies or endoscopies that did not establish the IBD diagnosis.

    Do not extract IBD family history, IBD negated, IBD rule-out, or IBD suspected/probable/working-diagnosis.
    """
    diagnosis_date_gold: str | None = Field(
        None,
        description=("Date of the endoscopic procedure that first established the IBD diagnosis, "
                     "in ISO YYYY-MM-DD format (e.g. 2021-01-15). Always emit a full YYYY-MM-DD value. "
                     "If only month or year precision is supported by the text, "
                     "use the first possible date consistent with it (January 2021 -> 2021-01-01; "
                     "2021 -> 2021-01-01) and record the actual precision in ibd_diagnosis_date_endoscopy_precision.")
    )

    diagnosis_date_gold_precision: DatePrecision | None = Field(
        None,
        description=("Precision actually supported by the source text for ibd_diagnosis_date_endoscopy. "
                     "DAY: day, month, and year were explicitly stated; "
                     "MONTH: month and year were explicitly stated; "
                     "YEAR: only year was explicitly stated; "
                     "Use Null when ibd_diagnosis_date_endoscopy is null.")
    )

###############################################################################
# Example: IBD Severity
###############################################################################
class DiseaseSeverity(StrEnum):
    """
    Current documented disease severity.

    These values intentionally include common clinician range phrases because
    LLM extraction quality is usually better when enum options closely match
    the language used in clinical notes.
    """
    MILD = "MILD"
    MILD_TO_MODERATE = "MILD_TO_MODERATE"
    MODERATE = "MODERATE"
    MODERATE_TO_SEVERE = "MODERATE_TO_SEVERE"
    SEVERE = "SEVERE"
    NONE_OF_THE_ABOVE = "NONE_OF_THE_ABOVE"

###############################################################################
# Example: IBD Activity
###############################################################################
class DiseaseActivity(StrEnum):
    """
    Current documented IBD disease activity.

    Use ACTIVE when the note documents current active disease, flare,
    ongoing inflammation, or active symptoms attributable to IBD.

    Use REMISSION when the note documents remission, quiescent disease,
    inactive disease, no active disease, or asymptomatic/inactive IBD as
    the current state.
    """
    REMISSION = "REMISSION"
    ACTIVE = "ACTIVE"
    NONE_OF_THE_ABOVE = "NONE_OF_THE_ABOVE"

class DiseaseActivityAndSeverityMention(SpanAugmentedMention):
    """
    Current documented IBD disease activity and severity.

    Examples:
    * "IBD in remission" -> activity=REMISSION, severity=NONE_OF_THE_ABOVE
    * "active Crohn's disease" -> activity=ACTIVE, severity=NONE_OF_THE_ABOVE
    * "mild disease" -> activity=ACTIVE, severity=MILD
    * "mild to moderate disease" -> activity=ACTIVE, severity=MILD_TO_MODERATE
    * "moderate disease" -> activity=ACTIVE, severity=MODERATE
    * "moderate to severe disease" -> activity=ACTIVE, severity=MODERATE_TO_SEVERE
    * "severe disease" -> activity=ACTIVE, severity=SEVERE

    If a severity is negated (e.g., "no severe disease"), do not assign that severity.

    If multiple severities appear for different anatomic segments
    (e.g., "severe proctitis with mild left-sided involvement"), use the highest severity.

    Do not infer severity from medication intensity, and do not use historical severity if the patient is now in remission.

    Do not extract family history of IBD, negated IBD, rule-out IBD, or suspected/probable/working-diagnosis IBD.
    """
    disease_activity: DiseaseActivity = Field(
        default=DiseaseActivity.NONE_OF_THE_ABOVE,
        description=(
            "Current documented IBD disease activity. "
            "ACTIVE: current active disease, active inflammation, active flare, "
            "currently flaring, or active IBD symptoms are documented and attributed to IBD; "
            "REMISSION: remission, quiescent disease, inactive disease, no active disease, "
            "or asymptomatic/inactive IBD is documented as the current state. "
            "NONE_OF_THE_ABOVE: current IBD activity is not documented."
        ),
    )

    disease_severity: DiseaseSeverity = Field(
        default=DiseaseSeverity.NONE_OF_THE_ABOVE,
        description=(
            "Current documented IBD disease severity. "
            "Use the enum value that best matches the clinician's wording. "
            "MILD: phrases such as 'mild disease' or 'mild activity'. "
            "MILD_TO_MODERATE: phrases such as 'mild to moderate disease'. "
            "MODERATE: phrases such as 'moderate disease' or 'moderate activity'. "
            "MODERATE_TO_SEVERE: phrases such as 'moderate to severe disease'. "
            "SEVERE: phrases such as 'severe disease' or 'severe activity'. "
            "NONE_OF_THE_ABOVE: severity is not documented, or only activity is documented "
            "without a severity grade, such as 'active disease' or 'active flare'."
        ),
    )

###############################################################################
# Aggregated Annotation and Mention Classes
#
# This is the top-level structure for the pydantic models used in IBD diagnosis.
###############################################################################
class DiseaseDiagnosisAnnotation(BaseModel):
    """
    Patient-level IBD diagnosis annotations extracted from a single clinical note.

    Captures the patient's IBD subtype, age at first diagnosis, first diagnosis date,
    diagnostic endoscopy date when documented, and current disease activity/severity.

    Do not extract family history of IBD, negated IBD, rule-out IBD, or suspected/probable/working-diagnosis IBD.
    """
    disease_type: DiseaseTypeMention
    age_at_diagnosis: AgeAtDiagnosisMention
    diagnosis_date: DiagnosisDateMention
    diagnosis_date_gold: DiagnosisDateGoldMention
    activity_and_severity: DiseaseActivityAndSeverityMention
