"""
SEE: https://loinc.org/58410-2

Complete Blood Count with Differential (CBC w/ diff) phenotype extraction schemas.

Models the standard CBC with 5-part differential (LOINC 58410-2) scoped to
analytes with direct relevance to pediatric IBD monitoring, thiopurine and
methotrexate toxicity surveillance, anemia phenotyping, and eosinophilic
GI disease differentiation.
"""
from pydantic import BaseModel
from cumulus_study_builder.llm.models.lab_base import LabValueMention

class HemoglobinMention(LabValueMention):
    """
    Blood hemoglobin concentration. Typically reported in g/dL or g/L.
    """
    pass


class HematocritMention(LabValueMention):
    """
    Hematocrit (packed cell volume). Typically reported as a percentage
    or a unitless fraction.
    """
    pass


class MCVMention(LabValueMention):
    """
    Mean corpuscular volume. Typically reported in fL. Used downstream
    to classify anemia as microcytic, normocytic, or macrocytic.
    """
    pass


class PlateletsMention(LabValueMention):
    """
    Platelet count. Typically reported as x10^3/uL, x10^9/L, or K/uL.
    Thrombocytosis is associated with active IBD.
    """
    pass

class WBCMention(LabValueMention):
    """
    White blood cell count. Elevated in active IBD inflammation and core
    to thiopurine and methotrexate myelosuppression surveillance. Typically
    reported as x10^3/uL, x10^9/L, or K/uL.
    """
    pass


class NeutrophilMention(LabValueMention):
    """
    Neutrophil count. Most clinically actionable component of the WBC
    differential in IBD: neutrophilia signals active inflammation and
    is mechanistically upstream of fecal calprotectin; absolute
    neutrophil count is the dose-limiting parameter for thiopurine and
    methotrexate safety monitoring; and persistent neutropenia in a
    young child with IBD-like colitis is a trigger for VEOIBD monogenic
    immunodeficiency workup (e.g., chronic granulomatous disease,
    congenital neutropenia, glycogen storage disease type 1b). When
    both absolute count (ANC, x10^3/uL or x10^9/L) and percentage are
    reported, capture the absolute count in value_numeric; record the
    percentage only when the absolute count is unavailable.
    """
    pass


class LymphocyteMention(LabValueMention):
    """
    Lymphocyte count. Lymphopenia is a recognized adverse effect of
    thiopurines and of anti-integrin and anti-trafficking biologics,
    and a marker of CMV reactivation risk under immunosuppression.
    When both absolute count (ALC) and percentage are reported, capture
    the absolute count in value_numeric; record the percentage only
    when the absolute count is unavailable.
    """
    pass


class EosinophilMention(LabValueMention):
    """
    Eosinophil count. Relevant at IBD diagnosis for the eosinophilic
    colitis differential, for identifying drug hypersensitivity
    reactions (5-ASA, thiopurines, biologics), and as a marker of
    allergic comorbidity. When both absolute count and percentage are
    reported, capture the absolute count in value_numeric; record the
    percentage only when the absolute count is unavailable.
    """
    pass


class MonocyteMention(LabValueMention):
    """
    Monocyte count. Non-specific marker of active inflammation,
    routinely reported on the CBC differential. When both absolute
    count and percentage are reported, capture the absolute count in
    value_numeric; record the percentage only when the absolute count
    is unavailable.
    """
    pass


# ---------------------------------------------------------------------------
# Annotation
# ---------------------------------------------------------------------------
class IbdCBCLabPanelAnnotation(BaseModel):
    """
    Complete blood count panel for pediatric IBD monitoring.

    * hemoglobin: Primary anemia indicator; reflects iron deficiency, chronic inflammation, or GI bleeding.
    * hematocrit: Corroborates hemoglobin; tracks anemia severity and treatment response longitudinally.
    * mcv: Discriminates iron-deficiency (microcytic) from B12/folate deficiency (macrocytic) or mixed anemia.
    * platelets: Thrombocytosis tracks with inflammatory burden; thrombocytopenia signals thiopurine toxicity.
    * wbc: Elevated in active inflammation or infection; depressed by thiopurine or methotrexate toxicity.
    * neutrophil: Primary thiopurine safety monitor; ANC threshold drives dose reduction or cessation.
    * lymphocyte: Depressed by methotrexate and corticosteroids; low counts elevate opportunistic infection risk.
    * eosinophil: Peripheral eosinophilia supports eosinophilic GI disease differential, especially in VEOIBD.
    * monocyte: Elevated in chronic inflammation; contributes to differential leukocyte pattern interpretation.
    """
    hemoglobin: HemoglobinMention
    hematocrit: HematocritMention
    mcv: MCVMention
    platelets: PlateletsMention
    wbc: WBCMention
    neutrophil: NeutrophilMention
    lymphocyte: LymphocyteMention
    eosinophil: EosinophilMention
    monocyte: MonocyteMention
