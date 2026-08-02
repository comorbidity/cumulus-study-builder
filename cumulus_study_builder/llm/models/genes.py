from enum import StrEnum
from pydantic import BaseModel, Field
from cumulus_study_builder.llm.models.base import SpanAugmentedMention

###############################################################################
# Clinical recommendations:
#   https://www.nice.org.uk/guidance/ng99/chapter/Recommendations
#
# NCBI Genetic Testing Registry
#   https://www.ncbi.nlm.nih.gov/gtr/conditions/C0017638/
###############################################################################


###############################################################################
# Genetic Variants
###############################################################################
class GeneticVariantInterpretation(StrEnum):
    BENIGN = "BENIGN"
    LIKELY_BENIGN = "LIKELY_BENIGN"
    VUS = "VUS"
    PATHOGENIC = "PATHOGENIC"
    LIKELY_PATHOGENIC = "LIKELY_PATHOGENIC"
    NONE_OF_THE_ABOVE = "NONE_OF_THE_ABOVE"

class GeneticVariantMention(SpanAugmentedMention):
    """
    Clinical interpretation of genetic variant
    """
    hgnc_name: str | None = Field(default=None, description="HGNC/HUGO gene naming convention")

    interpretation: GeneticVariantInterpretation = Field(
        GeneticVariantInterpretation.NONE_OF_THE_ABOVE,
        description="Clinical interpretation of genetic variant or genetic test result",
    )

    hgvs_variant: str | None = Field(
        None, description="HGVS variant string (e.g., NM_004333.6(BRAF):c.1799T>A)."
    )


###############################################################################
# Annotation BaseModel
###############################################################################
class ExampleGeneAnnotation(BaseModel):
    genetic_variant_mention: list[GeneticVariantMention] = Field(
        default_factory=list, description="All mentions of genetic variants"
    )
