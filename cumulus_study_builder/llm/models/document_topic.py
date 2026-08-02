"""Study-neutral topic-relevance selectors for LLM chart review.

The starter topics map to the generic extraction models in this package. Replace,
remove, or specialize them for the research objective. Keep the relevance contract
and one fixed top-level field per topic when human-readable wide Athena selectors are
desired.
"""

from enum import StrEnum

from pydantic import BaseModel, Field

from cumulus_study_builder.llm.models.base import SpanAugmentedMention


class TopicRelevance(StrEnum):
    """Highest level of evidence that a document contains for a requested topic."""

    EXPLICIT = "EXPLICIT"
    IMPLICIT = "IMPLICIT"
    NONE_OF_THE_ABOVE = "NONE_OF_THE_ABOVE"


class TopicRelevanceMention(SpanAugmentedMention):
    """Classify one defined study topic in one clinical document.

    Use patient-specific evidence unless the topic definition explicitly requests
    something else. By default, do not count negated, ruled-out, hypothetical, or
    family-history statements as relevant to the patient. Do not infer a clinical fact
    merely because a document type commonly contains it.
    """

    has_mention: bool = Field(
        ...,
        description=(
            "True exactly when relevance is EXPLICIT or IMPLICIT. "
            "False when relevance is NONE_OF_THE_ABOVE."
        ),
    )
    spans: list[str] = Field(
        ...,
        description=(
            "Shortest verbatim fragments that support this topic classification. "
            "Include direct topic language for EXPLICIT and supporting facts for "
            "IMPLICIT. Return an empty list for NONE_OF_THE_ABOVE."
        ),
    )
    relevance: TopicRelevance = Field(
        default=TopicRelevance.NONE_OF_THE_ABOVE,
        description=(
            "Choose the highest supported level. EXPLICIT: the topic is directly "
            "named, discussed, measured, scored, or otherwise clearly documented. "
            "IMPLICIT: the topic is not directly named, but the document contains the "
            "specific supporting evidence required by this topic's definition. "
            "NONE_OF_THE_ABOVE: neither explicit nor sufficient implicit evidence is present."
        ),
    )
    confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description=(
            "Confidence in the relevance classification from 0.0 to 1.0. For "
            "NONE_OF_THE_ABOVE, this is confidence that the document lacks sufficient "
            "topic evidence. Use null only when confidence cannot be estimated."
        ),
    )
    reasoning: str | None = Field(
        default=None,
        description=(
            "One concise sentence applying this topic's definition to the cited spans. "
            "Use null for NONE_OF_THE_ABOVE."
        ),
    )


class DiagnosisTopicRelevanceMention(TopicRelevanceMention):
    """Disease diagnosis or subtype documentation; routes to diagnosis extraction."""

    relevance: TopicRelevance = Field(
        default=TopicRelevance.NONE_OF_THE_ABOVE,
        description=(
            "EXPLICIT: a study disease, subtype, diagnostic assessment, or active "
            "diagnostic workup is directly named. "
            "IMPLICIT: the disease is not named, but the study's predefined minimum "
            "combination of diagnostic findings is documented. "
            "NONE_OF_THE_ABOVE: neither criterion is met."
        ),
    )


class DiseaseActivityTopicRelevanceMention(TopicRelevanceMention):
    """Current disease activity or severity; routes to activity extraction."""

    relevance: TopicRelevance = Field(
        default=TopicRelevance.NONE_OF_THE_ABOVE,
        description=(
            "EXPLICIT: current disease activity, remission, flare, severity, or a "
            "validated activity score is directly named or scored. "
            "IMPLICIT: activity is not named, but the study's predefined minimum "
            "symptom, examination, laboratory, or instrument components are present. "
            "NONE_OF_THE_ABOVE: neither criterion is met."
        ),
    )


class MedicationsTopicRelevanceMention(TopicRelevanceMention):
    """Study medication documentation; routes to treatment extraction."""

    relevance: TopicRelevance = Field(
        default=TopicRelevance.NONE_OF_THE_ABOVE,
        description=(
            "EXPLICIT: a medication or drug class relevant to the study is named. "
            "IMPLICIT: medication management is documented without a specific name, "
            "such as starting therapy, dose escalation, tapering, or an infusion. "
            "NONE_OF_THE_ABOVE: neither criterion is met."
        ),
    )


class LabsTopicRelevanceMention(TopicRelevanceMention):
    """Study laboratory testing; routes to laboratory extraction."""

    relevance: TopicRelevance = Field(
        default=TopicRelevance.NONE_OF_THE_ABOVE,
        description=(
            "EXPLICIT: a study-relevant laboratory analyte, result, value, unit, or "
            "interpretation is directly documented. "
            "IMPLICIT: laboratory testing is discussed qualitatively or planned "
            "without naming a study analyte or giving a result. "
            "NONE_OF_THE_ABOVE: neither criterion is met."
        ),
    )


class SurgeryTopicRelevanceMention(TopicRelevanceMention):
    """Study surgery documentation; routes to surgery extraction."""

    relevance: TopicRelevance = Field(
        default=TopicRelevance.NONE_OF_THE_ABOVE,
        description=(
            "EXPLICIT: a study-relevant surgical procedure is named as completed, "
            "planned, discussed, or part of the patient's history. "
            "IMPLICIT: surgery is not named, but study-defined postoperative anatomy, "
            "wound, stoma, or other surgical evidence is documented. "
            "NONE_OF_THE_ABOVE: neither criterion is met."
        ),
    )


class ImagingAndProcedureTopicRelevanceMention(TopicRelevanceMention):
    """Study imaging or non-operative procedure documentation."""

    relevance: TopicRelevance = Field(
        default=TopicRelevance.NONE_OF_THE_ABOVE,
        description=(
            "EXPLICIT: a study-relevant imaging study, diagnostic study, or "
            "non-operative procedure is named, planned, or documented with findings. "
            "IMPLICIT: the study or procedure is not named, but its study-defined "
            "findings are referenced in passing. "
            "NONE_OF_THE_ABOVE: neither criterion is met."
        ),
    )


class TopicRelevanceAnnotation(BaseModel):
    """Fixed, wide-friendly topic-routing gate for one clinical document.

    Replace or specialize these starter fields so each one maps to a downstream
    extraction task. Return every field, including topics with
    ``NONE_OF_THE_ABOVE`` relevance.
    """

    diagnosis: DiagnosisTopicRelevanceMention
    disease_activity: DiseaseActivityTopicRelevanceMention
    medications: MedicationsTopicRelevanceMention
    labs: LabsTopicRelevanceMention
    surgery: SurgeryTopicRelevanceMention
    imaging_and_procedure: ImagingAndProcedureTopicRelevanceMention


# Descriptive alias for callers that name the task after the source document.
DocumentTopicAnnotation = TopicRelevanceAnnotation
