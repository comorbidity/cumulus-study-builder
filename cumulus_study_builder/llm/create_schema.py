import os
import json
from pathlib import Path
from cumulus_study_builder.llm.models.treatment import ExampleTreatmentAnnotation
from cumulus_study_builder.llm.models.lab_base import ExampleLabPanelAnnotation

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
    """
    return [
        create(ExampleTreatmentAnnotation, 'example-treatment-annotation.json'),
        create(ExampleLabPanelAnnotation, 'example-lab-panel-annotation.json'),
    ]

if __name__ == "__main__":
    print('creating JSON schemas for Annotation(BaseModel)...')
    for p in create_all():
        print('\t', p)
