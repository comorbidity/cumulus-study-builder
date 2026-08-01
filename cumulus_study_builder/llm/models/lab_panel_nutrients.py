from pydantic import BaseModel
from cumulus_study_builder.llm.models.lab_base import LabValueMention

# ---------------------------------------------------------------------------
# Micronutrients
# ---------------------------------------------------------------------------
class FolateMention(LabValueMention):
    """
    Folate, measured in serum or red blood cells. Capture the reported
    specimen; serum folate and RBC folate have different reference ranges
    and clinical interpretations but are not disambiguated further at the
    extraction layer.
    """
    pass

class VitaminB12Mention(LabValueMention):
    """
    Vitamin B12 (cobalamin). Typically reported in pg/mL or pmol/L.
    Deficiency is associated with ileal disease and ileal resection.
    """
    pass


class VitaminDMention(LabValueMention):
    """
    25-hydroxyvitamin D. Typically reported in ng/mL or nmol/L (1 ng/mL
    = 2.5 nmol/L). Capture unit verbatim; do not normalize.
    """
    pass


class ZincMention(LabValueMention):
    """
    Serum or plasma zinc. Typically reported in ug/dL or umol/L.
    Deficiency is associated with malabsorption in IBD.
    """
    pass

# ---------------------------------------------------------------------------
# Annotation
# ---------------------------------------------------------------------------
class IbdNutrientsLabPanelAnnotation(BaseModel):
    """
    Nutritional micronutrient panel for pediatric IBD monitoring.

    * folate: Red cell or serum folate; depleted by small-bowel malabsorption and methotrexate.
    * vitamin_b12: Cobalamin; at risk in terminal ileal Crohn's disease or post-resection.
    * vitamin_d: 25-OH vitamin D; commonly deficient in IBD, compounds bone and immune risk.
    * zinc: Trace mineral lost via enteric inflammation and chronic diarrhea.
    """
    folate: FolateMention
    vitamin_b12: VitaminB12Mention
    vitamin_d: VitaminDMention
    zinc: ZincMention
