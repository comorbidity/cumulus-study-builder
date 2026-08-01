from pathlib import Path
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from cumulus_study_builder.tools import filetool
from cumulus_study_builder.tools.manifest import PREFIX

def load(file_sql: str, **kwargs) -> str:
    return _render(filetool.path_template(), file_sql, **kwargs)

def load_test(file_sql: str, **kwargs) -> str:
    return _render(filetool.path_tests_template(), file_sql, **kwargs)

def copy(file_sql: Path | str, **kwargs) -> Path:
    return _copy(filetool.path_template(), filetool.path_athena, file_sql, **kwargs)

def copy_test(file_sql: Path | str, **kwargs) -> Path:
    return _copy(filetool.path_tests_template(), filetool.path_tests_athena, file_sql, **kwargs)

def _render(template_dir: Path, file_sql: str, **kwargs) -> str:
    kwargs.setdefault("prefix", PREFIX)
    env = Environment(loader=FileSystemLoader(str(template_dir)),
                      undefined=StrictUndefined)
    return env.get_template(file_sql).render(**kwargs)

def _copy(template_dir: Path, athena_path, file_sql: Path | str, **kwargs) -> Path:
    file_name = file_sql.name if isinstance(file_sql, Path) else file_sql
    text = _render(template_dir, file_name, **kwargs)
    return filetool.write_text(text, athena_path(f"{PREFIX}__{file_name}"))
