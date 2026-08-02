"""
Complete Blood Count (CBC with differential) panel extraction.

SEE: https://loinc.org/58410-2

Generic CBC-with-differential example. One `LabBaseMention` subclass per analyte,
aggregated into a panel annotation. Each analyte inherits value_numeric, unit,
interpretation, and result date from LabBaseMention. Edit the analyte set and the
docstrings for your study.
"""
from pydantic import BaseModel
from cumulus_study_builder.llm.models.lab_base import LabBaseMention


class HemoglobinMention(LabBaseMention):
    """Blood hemoglobin concentration. Typically reported in g/dL or g/L."""
    pass


class HematocritMention(LabBaseMention):
    """Hematocrit (packed cell volume). Typically reported as a percentage or a
    unitless fraction."""
    pass


class MCVMention(LabBaseMention):
    """Mean corpuscular volume. Typically reported in fL. Used to classify red-cell
    size (microcytic, normocytic, macrocytic)."""
    pass


class PlateletsMention(LabBaseMention):
    """Platelet count. Typically reported as x10^3/uL, x10^9/L, or K/uL."""
    pass


class WBCMention(LabBaseMention):
    """White blood cell count. Typically reported as x10^3/uL, x10^9/L, or K/uL."""
    pass


class NeutrophilMention(LabBaseMention):
    """
    Neutrophil count. When both the absolute count (ANC, x10^3/uL or x10^9/L) and a
    percentage are reported, capture the absolute count in value_numeric and record
    the percentage only when the absolute count is unavailable.
    """
    pass


class LymphocyteMention(LabBaseMention):
    """
    Lymphocyte count. When both the absolute count (ALC) and a percentage are
    reported, capture the absolute count in value_numeric and record the percentage
    only when the absolute count is unavailable.
    """
    pass


class EosinophilMention(LabBaseMention):
    """
    Eosinophil count. When both the absolute count and a percentage are reported,
    capture the absolute count in value_numeric and record the percentage only when
    the absolute count is unavailable.
    """
    pass


class MonocyteMention(LabBaseMention):
    """
    Monocyte count. When both the absolute count and a percentage are reported,
    capture the absolute count in value_numeric and record the percentage only when
    the absolute count is unavailable.
    """
    pass


# ---------------------------------------------------------------------------
# Annotation
# ---------------------------------------------------------------------------
class CBCPanelAnnotation(BaseModel):
    """
    Complete blood count with differential. One documented result per analyte.

    Generic example — replace or trim the analytes to those your study needs.
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
