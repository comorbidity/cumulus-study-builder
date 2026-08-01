"""
SEE: https://loinc.org/24323-8

Comprehensive Metabolic Panel (CMP) phenotype extraction schemas.

Models the 14-analyte US CMP (LOINC 24323-8) plus the anion gap, which is
universally computed from CMP components and clinically relevant to IBD.
"""
from pydantic import BaseModel
from cumulus_study_builder.llm.models.lab_base import LabValueMention

# ---------------------------------------------------------------------------
# Electrolytes
# ---------------------------------------------------------------------------
class SodiumMention(LabValueMention):
    """
    Serum sodium. Relevant in IBD for assessing volume status and for
    hyponatremia in severe diarrhea, sepsis, or SIADH. Typically
    reported in mmol/L or mEq/L.
    """
    pass

class ChlorideMention(LabValueMention):
    """
    Serum chloride. Component of the anion gap calculation and of
    acid-base assessment in IBD patients with bicarbonate-losing
    diarrhea or high-output ileostomy. Typically reported in mmol/L
    or mEq/L.
    """
    pass

class TotalCalciumMention(LabValueMention):
    """
    Total Calcium. Used to monitor for malabsorption-driven hypocalcemia,
    vitamin D deficiency, and steroid-related bone metabolism disruption. Note that
    hypoalbuminemia may depress total calcium independently of ionized calcium.
    """
    pass

class PotassiumMention(LabValueMention):
    """
    Serum potassium. Hypokalemia is common in acute severe IBD and in
    patients with high-output diarrhea, ileostomy, or short bowel
    syndrome, and is a risk factor for ileus and cardiac arrhythmia.
    Typically reported in mmol/L or mEq/L.
    """
    pass

class BicarbonateMention(LabValueMention):
    """
    Serum bicarbonate (often reported as CO2 or total CO2 on a CMP).
    Low values indicate metabolic acidosis, commonly from high-output
    diarrhea or ileostomy losses in IBD; high values may reflect
    contraction alkalosis. Typically reported in mmol/L or mEq/L.
    """
    pass

class AnionGapMention(LabValueMention):
    """
    Anion gap, computed from sodium minus (chloride plus bicarbonate).
    Not formally part of the CMP but universally reported alongside it.
    Relevant in IBD for distinguishing high-gap acidosis (sepsis,
    lactic acidosis, ketoacidosis) from normal-gap acidosis
    (bicarbonate losses from diarrhea or ileostomy). Typically reported
    in mmol/L or mEq/L.
    """
    pass

# ---------------------------------------------------------------------------
# Protein
# ---------------------------------------------------------------------------
class TotalProteinMention(LabValueMention):
    """
    Total serum protein. Sum of albumin and globulins; interpreted
    alongside albumin to infer globulin fraction and to support
    assessment of protein-losing enteropathy and chronic inflammation
    in IBD. Typically reported in g/dL or g/L.
    """
    pass

class AlbuminMention(LabValueMention):
    """
    Serum albumin. Negative acute-phase reactant; hypoalbuminemia is
    associated with active IBD and protein-losing enteropathy.
    """
    pass

# ---------------------------------------------------------------------------
# Glucose
# ---------------------------------------------------------------------------
class GlucoseMention(LabValueMention):
    """
    Serum or plasma glucose. Relevant in IBD for corticosteroid-induced
    hyperglycemia surveillance and for identifying steroid-associated
    new-onset diabetes. Typically reported in mg/dL or mmol/L. Capture
    fasting status, if stated, in the spans; do not infer.
    """
    pass

# ---------------------------------------------------------------------------
# Liver Function Tests
# ---------------------------------------------------------------------------
class TotalBilirubinMention(LabValueMention):
    """
    Total bilirubin. Co-reported with transaminases and GGT for
    hepatobiliary assessment and drug hepatotoxicity monitoring.
    Typically reported in mg/dL or umol/L.
    """
    pass

class ALTMention(LabValueMention):
    """
    Alanine aminotransferase. Hepatocellular injury marker used for
    primary sclerosing cholangitis screening in pediatric IBD and for
    hepatotoxicity surveillance on thiopurines, methotrexate, and
    sulfasalazine. Typically reported in U/L or IU/L.
    """
    pass


class ASTMention(LabValueMention):
    """
    Aspartate aminotransferase. Hepatocellular injury marker co-reported
    with ALT for PSC screening and drug hepatotoxicity surveillance.
    Typically reported in U/L or IU/L.
    """
    pass

class AlkalinePhosphataseMention(LabValueMention):
    """
    Alkaline phosphatase. Cholestatic marker, though interpretation in
    pediatrics is limited by contribution from bone growth; GGT is
    preferred for PSC screening in this population. Typically reported
    in U/L or IU/L.
    """
    pass

# Liver function test ordered with CBC in Pediatric IBD patients.
class GGTMention(LabValueMention):
    """
    Gamma-glutamyl transferase. Cholestatic marker and the most sensitive
    biochemical signal for primary sclerosing cholangitis in pediatric
    IBD; pediatric alkaline phosphatase is unreliable due to growth-plate
    contribution. Typically reported in U/L or IU/L.
    """
    pass

# ---------------------------------------------------------------------------
# Kidney (Renal) function — BUN
# ---------------------------------------------------------------------------
class CreatinineMention(LabValueMention):
    """
    Serum creatinine. Primary laboratory marker of kidney function and a key
    denominator for the BUN-to-creatinine ratio. In pediatric IBD, creatinine
    helps assess dehydration, acute kidney injury, and medication-related renal
    toxicity. Typically reported in mg/dL or umol/L. Capture the reported value
    and unit verbatim; do not estimate eGFR at the extraction layer.
    """
    pass

class BUNMention(LabValueMention):
    """
    Blood urea nitrogen. Component of the renal panel and, in
    combination with creatinine, a marker of volume status in acute
    IBD flares and upper GI bleeding. Typically reported in mg/dL or
    mmol/L (as urea).
    """
    pass

class BUNCreatinineRatioMention(LabValueMention):
    """
    BUN-to-creatinine ratio. Not always reported separately, but when
    present, an elevated ratio supports prerenal azotemia from volume
    depletion in acute severe IBD. Unitless.
    """
    pass

# ---------------------------------------------------------------------------
# Annotation
# ---------------------------------------------------------------------------
class IbdCMPLabPanelAnnotation(BaseModel):
    """
    Comprehensive metabolic panel for pediatric IBD monitoring.

    # Electrolytes
    sodium: Serum sodium; depleted by chronic diarrhea and secretory loss.
    chloride: Serum chloride; tracks with sodium losses in high-output intestinal disease.
    potassium: Serum potassium; at risk in diarrhea, vomiting, and corticosteroid use.
    bicarbonate: Serum bicarbonate; metabolic acidosis marker in severe intestinal loss.
    anion_gap: Calculated gap; elevated in acidosis from malabsorption or septic complications.

    # Calcium
    calcium: Serum total calcium; depressed by malabsorption, vitamin D deficiency, and hypoalbuminemia.

    # Protein
    total_protein: Aggregate serum protein; declines with malnutrition and protein-losing enteropathy.
    albumin: Negative acute-phase reactant; surrogate for nutritional status and disease activity.

    # Glucose
    glucose: Serum glucose; monitored during corticosteroid therapy for steroid-induced hyperglycemia.

    # Liver (Hepatobiliary)
    total_bilirubin: Serum bilirubin; elevated in PSC, hemolysis, or thiopurine hepatotoxicity.
    ast: Hepatocellular injury marker; monitored for thiopurine and methotrexate DILI.
    alt: More liver-specific than AST; primary transaminase for DILI surveillance.
    alk_phos: Cholestatic marker; unreliable in pediatrics due to growth-plate contribution.
    ggt: may be ordered with CBC because alk_phos may be unreliable in pediatric IBD cases.

    # Renal
    bun: Blood urea nitrogen; elevated with dehydration, GI bleeding, or high protein catabolism.
    bun_creatinine_ratio: Prerenal vs intrinsic renal injury discriminator; elevated in GI bleeding.
    """
    # Electrolytes
    sodium: SodiumMention
    chloride: ChlorideMention
    potassium: PotassiumMention
    bicarbonate: BicarbonateMention
    anion_gap: AnionGapMention

    # Calcium
    calcium: TotalCalciumMention

    # Protein
    total_protein: TotalProteinMention
    albumin: AlbuminMention

    # Glucose
    glucose: GlucoseMention

    # Liver (Hepatobiliary)
    total_bilirubin: TotalBilirubinMention
    ast: ASTMention
    alt: ALTMention
    alk_phos: AlkalinePhosphataseMention
    ggt: GGTMention

    # Renal
    creatine: CreatinineMention
    bun: BUNMention
    bun_creatinine_ratio: BUNCreatinineRatioMention
