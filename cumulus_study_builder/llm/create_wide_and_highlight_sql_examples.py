# RECONSTRUCTED (approximate) — generic "flatten NLP result to a wide Athena
# table" example. The source study uses cumulus_library.BaseTableBuilder
# subclasses + an IbdFlatteningMixin (see llm/builder/); this starter renders a
# jinja UNNEST template directly for simplicity. Bring over the builder classes
# from your source study if you prefer that mechanism.
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from cumulus_study_builder.tools import filetool
from cumulus_study_builder.tools.manifest import PREFIX

TEMPLATE_DIR = filetool.path_llm_template()

def render(template_name: str, **kwargs) -> str:
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)), undefined=StrictUndefined)
    kwargs.setdefault("prefix", PREFIX)
    return env.get_template(template_name).render(**kwargs)

def make_example_wide(nlp_model: str = "gpt_oss_120b") -> Path:
    """
    Flatten an NLP result table `<prefix>__nlp_example_<model>` into
    `<prefix>__llm_example_wide` by UNNESTing the annotation arrays.
    """
    table_name = f"{PREFIX}__nlp_example_{nlp_model}"
    sql = render("example_wide.sql.jinja", table_names=[table_name])
    return filetool.save_llm_athena(f"{PREFIX}__llm_example_wide.sql", sql)

if __name__ == "__main__":
    print(make_example_wide())
