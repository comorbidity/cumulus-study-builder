import json
import os
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
    B = "BENIGN"
    LB = "LIKELY BENIGN"
    VUS = "VARIANT OF UNKNOWN SIGNIFICANCE"
    P = "PATHOGENIC"
    LP = "LIKELY PATHOGENIC"
    NOT_MENTIONED = "NOT MENTIONED"


class GeneticVariantMention(SpanAugmentedMention):
    """
    Clinical interpretation of genetic variant
    """
    hgnc_name: str | None = Field(default=None, description="HGNC/HUGO gene naming convention")

    interpretation: GeneticVariantInterpretation = Field(
        GeneticVariantInterpretation.NOT_MENTIONED,
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
