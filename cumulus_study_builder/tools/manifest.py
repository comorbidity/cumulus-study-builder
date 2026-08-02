import tomllib
import tomli_w
from pathlib import Path
from functools import lru_cache
from dataclasses import dataclass
from cumulus_library import StudyManifest
from cumulus_study_builder.tools import filetool

#-----------------------------------------------------------------------------
# Full cumulus-library StudyManifest (LAZY. do not call at import time).
#
# StudyManifest eagerly reads every submanifest TOML listed in manifest.toml
# (study_encounter.toml, study_variable.toml, ...). Those submanifests are GENERATED
# by the tools/*.py generators, so on a fresh checkout they do not exist yet.
# Building the full manifest at import time would dead-lock the bootstrap. you could
# not run the generators that create the very files the manifest needs. So keep this
# lazy. call get_manifest() only after the submanifests have been generated (e.g.
# from build tooling that needs the validated manifest). The generators themselves
# only need the study prefix, read directly below.
#-----------------------------------------------------------------------------
@lru_cache(maxsize=1)
def get_manifest(manifest_path: Path | str = None) -> StudyManifest:
    if not manifest_path:
        manifest_path = filetool.path_project()
    if isinstance(manifest_path, str):
        manifest_path = filetool.path_project(manifest_path)
    return StudyManifest(manifest_path)

#-----------------------------------------------------------------------------
# Study prefix. Read straight from manifest.toml (lightweight, no eager subconfig
# load) so the generators bootstrap on a fresh checkout. Keep identical to PREFIX in
# tools/tablespace.py. All tables are named <PREFIX>__<table>.
#-----------------------------------------------------------------------------
def get_study_prefix() -> str:
    with open(filetool.path_project('manifest.toml'), 'rb') as f:
        return tomllib.load(f)['study_prefix']

PREFIX = get_study_prefix()

#-----------------------------------------------------------------------------
# TOML action declarations
#-----------------------------------------------------------------------------
@dataclass(frozen=True)
class FileAction:
    file_list: list[Path] | list[str]
    description: str = ""
    build_type: str = "build:serial"

@dataclass(frozen=True)
class SqlAction:
    file_list: list[Path] | list[str]
    description: str = ""
    build_type: str = "build:parallel"

@dataclass(frozen=True)
class ExportAction:
    file_list: list[Path] | list[str]
    description: str = ""
    export_type: str = "export:counts"

#-----------------------------------------------------------------------------
# TOML builders
#-----------------------------------------------------------------------------
def as_sql_toml(actions: SqlAction | list[SqlAction]) -> dict:
    return as_actions_toml(_as_list(actions))

def as_export_toml(actions: ExportAction | list[ExportAction]) -> dict:
    return as_actions_toml(_as_list(actions))

def as_actions_toml(actions) -> dict:
    return {"actions": [_action_to_dict(action) for action in _as_list(actions)]}

def as_file_upload_toml(file_list: list[Path], prefix: str | None = None) -> dict:
    tables: dict[str, dict[str, str]] = {}
    for filename in file_list:
        simple = filetool.file_to_simplename(filename.name)
        if prefix is None:
            table_name = simple if "include" in filename.name else f"valueset_{simple}"
        else:
            table_name = f"{prefix}{simple}"
        tables[table_name] = {"file": filename.name}
    return {"config_type": "file_upload", "tables": tables}

#-----------------------------------------------------------------------------
# TOML save helpers
#-----------------------------------------------------------------------------
def save_actions_toml(actions, toml_file: Path | str) -> Path:
    return save_toml(content=as_actions_toml(actions), toml_file=toml_file)

def save_file_upload_toml(file_list: list[Path], toml_file: Path | str, prefix: str | None = None) -> Path:
    if not isinstance(toml_file, Path):
        toml_file = filetool.path_spreadsheet(toml_file)
    return save_toml(content=as_file_upload_toml(file_list, prefix), toml_file=toml_file)

def save_toml(content: dict | list[dict], toml_file: Path | str) -> Path:
    if not isinstance(toml_file, Path):
        toml_file = filetool.path_project(toml_file)
    content = _merge_toml_sections(content) if isinstance(content, list) else content
    return save_text_toml(dumps_toml(content), toml_file)

def save_lines_toml(lines: list[str], toml_file: Path | str) -> Path:
    if not isinstance(toml_file, Path):
        toml_file = filetool.path_project(toml_file)
    return save_text_toml("\n".join(lines), toml_file)

def save_text_toml(content: str, toml_file: Path | str) -> Path:
    if not isinstance(toml_file, Path):
        toml_file = filetool.path_project(toml_file)
    return filetool.write_text(content.strip() + "\n", toml_file)

#-----------------------------------------------------------------------------
# TOML helpers
#-----------------------------------------------------------------------------
def _clean_description(description: str | None = None) -> str:
    if not description:
        return ""
    return description.replace("[", "(").replace("]", ")")

def _action_to_dict(action) -> dict:
    if isinstance(action, SqlAction):
        return {"description": _clean_description(action.description),
                "type": action.build_type or "",
                "files": [f"athena/{f.name}" for f in action.file_list]}
    if isinstance(action, FileAction):
        return {"description": _clean_description(action.description),
                "type": action.build_type or "",
                "files": [f for f in action.file_list]}
    if isinstance(action, ExportAction):
        return {"description": _clean_description(action.description),
                "type": action.export_type or "",
                "tables": [f.stem for f in action.file_list]}
    if isinstance(action, dict):
        return action

def _as_list(item):
    return item if isinstance(item, list) else [item]

def _merge_toml_sections(content: list[dict]) -> dict:
    merged: dict = {}
    for section in content:
        for key, value in section.items():
            if key == "actions":
                merged.setdefault("actions", [])
                merged["actions"].extend(value or [])
            elif key == "tables":
                merged.setdefault("tables", {})
                duplicate_tables = set(merged["tables"]).intersection(value or {})
                if duplicate_tables:
                    duplicates = ", ".join(sorted(duplicate_tables))
                    raise ValueError(f"Duplicate TOML table names: {duplicates}")
                merged["tables"].update(value or {})
            elif key not in merged:
                merged[key] = value
            elif merged[key] != value:
                raise ValueError(f"Conflicting TOML value for key {key!r}: {merged[key]!r} != {value!r}")
    return merged

def dumps_toml(content: dict) -> str:
    return tomli_w.dumps(content)
