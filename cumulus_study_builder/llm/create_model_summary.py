# RECONSTRUCTED (approximate) — generic model->text summary generator.
# Replace with the source `create_model_summary.py` on device sync for the exact
# formatting. Walks a Pydantic Annotation and writes a human-readable summary of
# its fields, enum options, and descriptions to summaries/<name>_summary.txt.
import enum
import pathlib
import pydantic
from typing import Any, get_args, get_origin, Union
from types import UnionType

from cumulus_study_builder.llm.models.treatment import ExampleTreatmentAnnotation
from cumulus_study_builder.llm.models.lab_base import ExampleLabPanelAnnotation
from cumulus_study_builder.llm.models.lab_panel_cbc import CBCPanelAnnotation
from cumulus_study_builder.llm.models.lab_panel_cmp import CMPPanelAnnotation
from cumulus_study_builder.llm.models.lab_panel_iron import IronStudiesAnnotation
from cumulus_study_builder.llm.models.diagnosis import DiseaseDiagnosisAnnotation
from cumulus_study_builder.llm.models.surgery import SurgeryAnnotation
from cumulus_study_builder.llm.models.document_type import DocumentTypeAnnotation
from cumulus_study_builder.llm.models.document_topic import TopicRelevanceAnnotation

BASE_DIR = pathlib.Path(__file__).resolve().parent
_INDENT = "    "
_IGNORE_FIELDS = {"has_mention", "spans"}


def _field_description(field: Any) -> str | None:
    if hasattr(field, "description") and field.description:
        return field.description
    return None


def _is_model_type(tp: Any) -> bool:
    return isinstance(tp, type) and issubclass(tp, pydantic.BaseModel)


def _is_enum_type(tp: Any) -> bool:
    return isinstance(tp, type) and issubclass(tp, enum.Enum)


def _unwrap(tp: Any):
    """Unwrap Optional[...] / list[...] to the inner meaningful type."""
    origin = get_origin(tp)
    if origin in (Union, UnionType):
        args = [a for a in get_args(tp) if a is not type(None)]
        return _unwrap(args[0]) if args else tp
    if origin in (list, set, tuple):
        args = get_args(tp)
        return _unwrap(args[0]) if args else tp
    return tp


def _summarize(model_cls, depth=0, seen=None) -> list[str]:
    seen = seen or set()
    if model_cls in seen:
        return []
    seen.add(model_cls)
    lines = []
    doc = (model_cls.__doc__ or "").strip()
    if doc:
        lines.append(_INDENT * depth + doc.splitlines()[0])
    for name, field in model_cls.model_fields.items():
        if name in _IGNORE_FIELDS:
            continue
        inner = _unwrap(field.annotation)
        desc = _field_description(field)
        head = f"{_INDENT * depth}- {name}"
        if desc:
            head += f": {desc}"
        lines.append(head)
        if _is_enum_type(inner):
            for member in inner:
                lines.append(f"{_INDENT * (depth + 1)}* {member.value}")
        elif _is_model_type(inner):
            lines.extend(_summarize(inner, depth + 1, seen))
    return lines


def create(annotation, filename: str) -> pathlib.Path:
    out = BASE_DIR / "summaries" / filename
    out.parent.mkdir(parents=True, exist_ok=True)
    text = "\n".join(_summarize(annotation))
    out.write_text(text + "\n", encoding="utf8")
    return out


def create_all() -> list[pathlib.Path]:
    return [
        create(ExampleTreatmentAnnotation, "example_treatment_summary.txt"),
        create(ExampleLabPanelAnnotation,  "example_lab_panel_summary.txt"),
        create(CBCPanelAnnotation,         "cbc_panel_summary.txt"),
        create(CMPPanelAnnotation,         "cmp_panel_summary.txt"),
        create(IronStudiesAnnotation,      "iron_studies_summary.txt"),
        create(DiseaseDiagnosisAnnotation, "diagnosis_summary.txt"),
        create(SurgeryAnnotation,          "surgery_summary.txt"),
        create(DocumentTypeAnnotation,     "document_type_summary.txt"),
        create(TopicRelevanceAnnotation,   "topic_relevance_summary.txt"),
    ]


if __name__ == "__main__":
    for p in create_all():
        print(p)
