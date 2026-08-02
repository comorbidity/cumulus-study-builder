import unittest
from pathlib import Path
from cumulus_study_builder.tools import filetool, manifest, template

UNION_TABLES = 'union_tables'
DROP_TABLES = 'drop_tables'

def list_templates() -> list[Path]:
    return sorted(list(filetool.path_tests_template().glob("*.sql")))

def list_athena() -> list[Path]:
    return sorted(filter_list(list(filetool.path_tests_athena().glob("*.sql"))))

def list_tables() -> list[str]:
    return [file.stem for file in filter_list(list_athena())]

def filter_list(item_list):
    ignore = [DROP_TABLES, UNION_TABLES]
    for item in item_list:
        if isinstance(item, Path):
            if item.stem not in ignore:
                yield item
        else:
            if item not in ignore:
                yield item

def union_tables() -> Path:
    from cumulus_study_builder.tools.tablespace import name_prefix
    ctas = f"CREATE TABLE {name_prefix('qa_union_all')} AS "
    text = [f"SELECT COUNT(*) AS cnt, '{table}' AS test\nFROM {table}" for table in list_tables()]
    text = ctas + '\n' + '\n UNION ALL \n'.join(text) if text else ctas + "\n SELECT 0 as cnt, 'none' as test"
    return filetool.write_text(text, filetool.path_tests_athena(f"{UNION_TABLES}.sql"))

def drop_tables() -> Path:
    text = [f"DROP TABLE IF EXISTS {table}" for table in list_tables()]
    return filetool.write_text(';\n'.join(text), filetool.path_tests_athena(f"{DROP_TABLES}.sql"))

def relative_to_athena(path_list) -> list[str]:
    return [f'../tests/athena/{file.name}' for file in path_list]

def make() -> Path:
    for t in list_templates():
        template.copy_test(t)
    actions = [
        manifest.FileAction(
            relative_to_athena(list_athena()),
            description="all tables should have zero rows",
            build_type='build:parallel'),
        manifest.FileAction(
            relative_to_athena([union_tables()]),
            description="union tests")]
    return manifest.save_actions_toml(actions, 'test.toml')

class TestEncounterRefLink(unittest.TestCase):
    @unittest.skip("manual verification")
    def test_make(self):
        print(make())
