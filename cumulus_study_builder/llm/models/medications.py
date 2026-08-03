# To specialize: add an RxClass StrEnum with the drug classes your study needs,
# add response/adverse-event mentions if your objective requires them, and put
# the exact medication names/brands in the supporting spans. Keep every enum
# parsimonious — only values that drive a decision (inclusion/exclusion,
# treatment change, or outcome).
from enum import StrEnum
from pydantic import BaseModel, Field
from cumulus_study_builder.llm.models.base import SpanAugmentedMention, DatePrecision

# ExampleMedicationAnnotation
# └── rx_annotations: list[RxAnnotation]
#     ├── rx_start_date: RxStartDateMention
#     ├── rx_class: RxClassMention
#     ├── rx_status: RxStatusMention
#     ├── rx_response: RxResponseMention
#     └── rx_adverse_drug_events: list[RxAdverseDrugEventMention]

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

class RxClass(StrEnum):
    """
    Medication Class. 
    This is placeholder for researchers to modify with study-specific drug classes. 
    """
    CHEMOTHERAPY = "CHEMOTHERAPY"
    CORTICOSTEROID = "CORTICOSTEROID"
    IMMUNOMODULATOR = "IMMUNOMODULATOR"    
    NONE_OF_THE_ABOVE = "NONE_OF_THE_ABOVE"

class RxClassMention(SpanAugmentedMention):
    """
    A mention of a medication class in the clinical record.

    Assign by pharmacologic class only. The supporting span should include the
    exact medication name, brand name, biosimilar name, abbreviation, or class
    phrase when present.
    """
    rx_class: RxClass = Field(
        RxClass.NONE_OF_THE_ABOVE,
        description=(
            "Medication class for this medication. Choose one: "
            "CHEMOTHERAPY: todo write a description here; "
            "CORTICOSTEROID: todo write a description here; "
            "IMMUNOMODULATOR: todo write a description here; "            
            "NONE_OF_THE_ABOVE: if no medication class can be inferred, the class is unclear, "
            "or the medication is outside these classes"
        ),
    )

class RxResponse(StrEnum):
    RESPONSE_OR_REMISSION = "RESPONSE_OR_REMISSION"
    PARTIAL_RESPONSE = "PARTIAL_RESPONSE"
    PRIMARY_NON_RESPONSE = "PRIMARY_NON_RESPONSE"
    LOSS_OF_RESPONSE = "LOSS_OF_RESPONSE"
    NONE_OF_THE_ABOVE = "NONE_OF_THE_ABOVE"

class RxResponseMention(SpanAugmentedMention):
    """
    Documented response of IBD disease activity to a specific medication.
    Response is attributed to the medication, not overall disease course.
    """
    rx_response: RxResponse = Field(
        RxResponse.NONE_OF_THE_ABOVE,
        description=(
            "IBD medication response for this medication. Choose one: "
            "RESPONSE_OR_REMISSION: documented improvement, clinical response, clinical remission, "
            "or sustained good control on this medication, with no later loss of effect noted; "
            "PARTIAL_RESPONSE: documented improvement but incomplete remission or persistent disease activity; "
            "PRIMARY_NON_RESPONSE: no meaningful initial response after an adequate induction or initial treatment trial; "
            "LOSS_OF_RESPONSE: initial response or remission followed later by recurrent symptoms, flare, "
            "dose escalation, switch, or discontinuation for active disease; "            
            "NONE_OF_THE_ABOVE: response not mentioned, or not captured by these options."
        )
    )

class RxAdverseDrugEvent(StrEnum):
    """
    Adverse drug event category for medications, scoped to events that
    plausibly drive a change in therapy (discontinuation, switch, or
    escalation). Categories are intentionally broad and chart-review friendly.
    """
    LIVER = "LIVER"
    KIDNEY = "KIDNEY"
    METABOLISM = "METABOLISM"
    HEART = "HEART"
    BLOOD = "BLOOD"
    SKIN = "SKIN"
    NEURO = "NEURO"
    NONE_OF_THE_ABOVE = "NONE_OF_THE_ABOVE"

class RxAdverseDrugEventMention(SpanAugmentedMention):
    """
    A mention of an adverse drug event (ADE) attributed to an medication.

    Use only when the chart links the event to medication toxicity, intolerance,
    allergy, reaction, or complication. Do not classify ordinary IBD symptoms as
    ADEs unless the note documents them as medication-related.
    """
    ade: RxAdverseDrugEvent = Field(
        RxAdverseDrugEvent.NONE_OF_THE_ABOVE,
        description=(
            "Treatment-limiting ADE category for this medication, when the note attributes the ADE to the drug. "
            "Choose one: "
            "LIVER: elevated liver enzymes, hepatitis, hepatotoxicity, or liver injury; "
            "KIDNEY: nephrotoxicity, nephritis, renal injury, AKI, or kidney dysfunction; "
            "METABOLISM: TODO write a description here;"
            "HEART: TODO write a description here;"
            "BLOOD: low WBC, leukopenia, neutropenia, anemia, thrombocytopenia, pancytopenia, or bone marrow suppression; "                        
            "SKIN: non-cancer skin toxicity, such as rash, psoriasis, eczema, alopecia, "
            "severe skin reaction, or acneiform eruption; "
            "NEURO: demyelination, neuropathy, seizure, PML, or severe neurologic toxicity; "
            "NONE_OF_THE_ABOVE: no drug-attributed ADE, event is not treatment-limiting, "
            "or the ADE does not fit any category above. "
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
    rx_class: RxClassMention
    rx_status: RxStatusMention
    rx_start_date: RxStartDateMention
    rx_response: RxResponseMention
    rx_adverse_drug_events: list[RxAdverseDrugEventMention] = Field(
        default_factory=list,
        description=(
            "ADE(s) attributed to this medication or medication class. "
            "Create one mention per ADE category. Leave empty if no ADE is documented "
            "for this medication context."
        ),
    )

class ExampleMedicationAnnotation(BaseModel):
    """
    EXAMPLE medication annotation. Create one RxAnnotation per medication context.
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
