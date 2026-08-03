import os
import json
from pathlib import Path

from cumulus_study_builder.llm.models.medications import ExampleMedicationAnnotation
from cumulus_study_builder.llm.models.lab_base import ExampleLabPanelAnnotation
from cumulus_study_builder.llm.models.lab_panel_cbc import CBCPanelAnnotation
from cumulus_study_builder.llm.models.lab_panel_cmp import CMPPanelAnnotation
from cumulus_study_builder.llm.models.lab_panel_iron import IronPanelAnnotation
from cumulus_study_builder.llm.models.diagnosis import DiseaseDiagnosisAnnotation
from cumulus_study_builder.llm.models.surgery import SurgeryAnnotation
from cumulus_study_builder.llm.models.document_type import DocumentTypeAnnotation
from cumulus_study_builder.llm.models.document_topic import TopicRelevanceAnnotation

BASE_DIR = Path(os.path.dirname(__file__))

def create(annotation, filename: str) -> Path:
    """
    Create a JSON schema from a Pydantic Annotation via model_json_schema().
    This JSON is the LLM extraction contract used by the NLP task.
    """
    file_path = BASE_DIR / 'schemas' / filename
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf8") as f:
        json.dump(annotation.model_json_schema(), f, indent=2)
    return file_path

def create_all() -> list[Path]:
    """
    Register each chart-review Annotation here. Add a `create(...)` line per model.
    These are generic examples — rename, trim, or replace them for your study.
    """
    return [
        create(ExampleMedicationAnnotation, 'example-medication-annotation.json'),
        create(ExampleLabPanelAnnotation,  'example-lab-panel-annotation.json'),
        create(CBCPanelAnnotation,         'cbc-panel-annotation.json'),
        create(CMPPanelAnnotation,         'cmp-panel-annotation.json'),
        create(IronPanelAnnotation, 'iron-studies-annotation.json'),
        create(DiseaseDiagnosisAnnotation, 'diagnosis-annotation.json'),
        create(SurgeryAnnotation,          'surgery-annotation.json'),
        create(DocumentTypeAnnotation,     'document-type-annotation.json'),
        create(TopicRelevanceAnnotation,   'topic-relevance-annotation.json'),
    ]

if __name__ == "__main__":
    print('creating JSON schemas for Annotation(BaseModel)...')
    for p in create_all():
        print('\t', p)
