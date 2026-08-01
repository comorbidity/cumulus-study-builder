from enum import StrEnum
from pydantic import BaseModel, Field

class SpanAugmentedMention(BaseModel):
    """
    A mention of a particular concept in the text, augmented with the character spans
    where the mention was found.
    This allows for validation of LLM-generated findings, as well as the ability to link
    mentions back to the original text for review and auditing purposes.
    """
    has_mention: bool = Field(
        ...,
        description='Indicates whether the concept was mentioned in the text.'
    )
    spans: list[str] = Field(
        ...,
        description='The verbatim text where this concept was mentioned.'
    )

################################################################
# How to use DatePrecision
# $YOUR_DATE is the name of your date variable, e.g. "rx_start_date"
#
# description=
# "Precision actually supported by the source text for $YOUR_DATE. "
# "DAY: day, month, and year were explicitly stated; "
# "MONTH: month and year were explicitly stated; "
# "YEAR: only year was explicitly stated; "
# "Use Null when $YOUR_DATE is null."
################################################################
class DatePrecision(StrEnum):
    DAY = "DAY"
    MONTH = "MONTH"
    YEAR = "YEAR"
