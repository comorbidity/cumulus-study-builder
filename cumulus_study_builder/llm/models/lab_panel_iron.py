from pydantic import BaseModel
from cumulus_study_builder.llm.models.lab_base import LabValueMention

# ---------------------------------------------------------------------------
# Iron studies
# ---------------------------------------------------------------------------
class IronMention(LabValueMention):
    """
    Serum iron. Circulating iron bound largely to transferrin. Interpreted
    alongside ferritin, transferrin, TIBC, and transferrin saturation for
    anemia phenotyping in IBD. Typically reported in ug/dL or umol/L. Capture
    the reported value and unit verbatim; do not infer iron deficiency from the
    value alone.
    """
    pass

class TIBCMention(LabValueMention):
    """
    Total iron-binding capacity. Typically reported in ug/dL or umol/L.
    """
    pass

class FerritinMention(LabValueMention):
    """
    Serum ferritin. Iron storage protein and positive acute-phase reactant;
    interpretation in IBD requires co-assessment with CRP. Typically
    reported in ng/mL or ug/L.
    """
    pass

class TransferrinMention(LabValueMention):
    """
    Serum transferrin. Iron transport protein. Typically reported in
    mg/dL or g/L.
    """
    pass

class TransferrinSaturationMention(LabValueMention):
    """
    Transferrin saturation (TSAT), computed as serum iron divided by
    TIBC. Typically reported as a percentage. Low TSAT is a sensitive
    marker of iron deficiency in IBD even when ferritin is elevated by
    inflammation.
    """
    pass

# ---------------------------------------------------------------------------
# Annotation
# ---------------------------------------------------------------------------
class IbdIronLabPanelAnnotation(BaseModel):
    """
    Iron studies panel for anemia evaluation in pediatric IBD.
    https://loinc.org/75689-0

    * tibc: Total iron-binding capacity; elevated in iron deficiency, suppressed in inflammation.
    * ferritin: Acute-phase reactant; interpret cautiously as iron store marker in active disease.
    * transferrin: Iron transport protein; inversely tracks iron status but depressed by inflammation.
    * transferrin_saturation: Ferritin/TIBC ratio; best functional indicator of iron-deficient erythropoiesis.
    """
    iron: IronMention
    tibc: TIBCMention
    ferritin: FerritinMention
    transferrin: TransferrinMention
    transferrin_saturation: TransferrinSaturationMention
