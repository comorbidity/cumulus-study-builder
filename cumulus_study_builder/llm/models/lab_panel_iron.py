"""
Iron studies panel extraction.

SEE: https://loinc.org/75689-0

Generic iron-studies example (the analytes typically ordered together to evaluate iron
status). One `LabBaseMention` subclass per analyte, aggregated into a panel annotation.
Edit the analyte set and docstrings for your study.
"""
from pydantic import BaseModel
from cumulus_study_builder.llm.models.lab_base import LabBaseMention


class IronMention(LabBaseMention):
    """Serum iron. Typically reported in ug/dL or umol/L. Capture the reported value
    and unit verbatim; do not infer iron status from the value alone."""
    pass


class TIBCMention(LabBaseMention):
    """Total iron-binding capacity (TIBC). Typically reported in ug/dL or umol/L."""
    pass


class FerritinMention(LabBaseMention):
    """Serum ferritin. An iron-storage protein and a positive acute-phase reactant.
    Typically reported in ng/mL or ug/L."""
    pass


class TransferrinMention(LabBaseMention):
    """Serum transferrin (iron transport protein). Typically reported in mg/dL or g/L."""
    pass


class TransferrinSaturationMention(LabBaseMention):
    """Transferrin saturation (TSAT), computed as serum iron divided by TIBC. Typically
    reported as a percentage."""
    pass


# ---------------------------------------------------------------------------
# Annotation
# ---------------------------------------------------------------------------
class IronStudiesAnnotation(BaseModel):
    """
    Iron studies panel. One documented result per analyte.

    Generic example — replace or trim the analytes to those your study needs.
    """
    iron: IronMention
    tibc: TIBCMention
    ferritin: FerritinMention
    transferrin: TransferrinMention
    transferrin_saturation: TransferrinSaturationMention
