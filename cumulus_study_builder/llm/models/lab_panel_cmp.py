"""
Comprehensive / Basic Metabolic Panel (CMP / BMP) extraction.

SEE: https://loinc.org/24323-8

Generic CMP example (drop the liver-function and protein analytes for a BMP). One
`LabBaseMention` subclass per analyte, aggregated into a panel annotation. Edit the
analyte set and docstrings for your study.
"""
from pydantic import BaseModel
from cumulus_study_builder.llm.models.lab_base import LabBaseMention


# ---------------------------------------------------------------------------
# Electrolytes
# ---------------------------------------------------------------------------
class SodiumMention(LabBaseMention):
    """Serum sodium. Typically reported in mmol/L or mEq/L."""
    pass


class ChlorideMention(LabBaseMention):
    """Serum chloride. Component of the anion-gap calculation. Typically reported in
    mmol/L or mEq/L."""
    pass


class PotassiumMention(LabBaseMention):
    """Serum potassium. Typically reported in mmol/L or mEq/L."""
    pass


class BicarbonateMention(LabBaseMention):
    """Serum bicarbonate (often reported as CO2 or total CO2 on a CMP). Typically
    reported in mmol/L or mEq/L."""
    pass


class AnionGapMention(LabBaseMention):
    """Anion gap, computed from sodium minus (chloride plus bicarbonate). Reported
    alongside the CMP though not a measured analyte. Typically unitless or mmol/L."""
    pass


# ---------------------------------------------------------------------------
# Calcium / Protein
# ---------------------------------------------------------------------------
class TotalCalciumMention(LabBaseMention):
    """Total calcium. May be depressed by hypoalbuminemia independently of ionized
    calcium. Typically reported in mg/dL or mmol/L."""
    pass


class TotalProteinMention(LabBaseMention):
    """Total serum protein (albumin plus globulins). Typically reported in g/dL or g/L."""
    pass


class AlbuminMention(LabBaseMention):
    """Serum albumin. A negative acute-phase reactant. Typically reported in g/dL or g/L."""
    pass


# ---------------------------------------------------------------------------
# Glucose
# ---------------------------------------------------------------------------
class GlucoseMention(LabBaseMention):
    """Serum or plasma glucose. Typically reported in mg/dL or mmol/L. Capture fasting
    status, if stated, in the spans; do not infer it."""
    pass


# ---------------------------------------------------------------------------
# Liver function tests (drop these for a BMP)
# ---------------------------------------------------------------------------
class TotalBilirubinMention(LabBaseMention):
    """Total bilirubin. Typically reported in mg/dL or umol/L."""
    pass


class ALTMention(LabBaseMention):
    """Alanine aminotransferase (ALT). Hepatocellular injury marker. Typically reported
    in U/L or IU/L."""
    pass


class ASTMention(LabBaseMention):
    """Aspartate aminotransferase (AST). Hepatocellular injury marker. Typically
    reported in U/L or IU/L."""
    pass


class AlkalinePhosphataseMention(LabBaseMention):
    """Alkaline phosphatase. Cholestatic marker (pediatric values include a bone-growth
    contribution). Typically reported in U/L or IU/L."""
    pass


class GGTMention(LabBaseMention):
    """Gamma-glutamyl transferase (GGT). Cholestatic marker; sometimes ordered when
    alkaline phosphatase is unreliable. Typically reported in U/L or IU/L."""
    pass


# ---------------------------------------------------------------------------
# Renal
# ---------------------------------------------------------------------------
class CreatinineMention(LabBaseMention):
    """Serum creatinine. Primary marker of kidney function. Typically reported in
    mg/dL or umol/L. Capture the reported value and unit verbatim; do not estimate eGFR
    at the extraction layer."""
    pass


class BUNMention(LabBaseMention):
    """Blood urea nitrogen (BUN). Typically reported in mg/dL or mmol/L (as urea)."""
    pass


class BUNCreatinineRatioMention(LabBaseMention):
    """BUN-to-creatinine ratio, when reported separately. Unitless."""
    pass


# ---------------------------------------------------------------------------
# Annotation
# ---------------------------------------------------------------------------
class CMPPanelAnnotation(BaseModel):
    """
    Comprehensive metabolic panel. One documented result per analyte. Drop the liver
    and protein analytes for a basic metabolic panel (BMP).

    Generic example — replace or trim the analytes to those your study needs.
    """
    # Electrolytes
    sodium: SodiumMention
    chloride: ChlorideMention
    potassium: PotassiumMention
    bicarbonate: BicarbonateMention
    anion_gap: AnionGapMention

    # Calcium / Protein
    calcium: TotalCalciumMention
    total_protein: TotalProteinMention
    albumin: AlbuminMention

    # Glucose
    glucose: GlucoseMention

    # Liver function
    total_bilirubin: TotalBilirubinMention
    ast: ASTMention
    alt: ALTMention
    alk_phos: AlkalinePhosphataseMention
    ggt: GGTMention

    # Renal
    creatinine: CreatinineMention
    bun: BUNMention
    bun_creatinine_ratio: BUNCreatinineRatioMention
