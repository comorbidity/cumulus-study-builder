from pathlib import Path
from cumulus_study_builder.tools import manifest, template

DATA_PACKAGE_VERSION = 1

def make_study_meta_sql(data_package_version:int = DATA_PACKAGE_VERSION) -> list[Path]:
    return [template.copy(f"meta_date.sql"),
            template.copy(f"meta_version.sql", data_package_version=str(data_package_version))]

def make_actions() -> list[manifest.SqlAction | manifest.ExportAction]:
    file_list = make_study_meta_sql()
    return [
        manifest.SqlAction(file_list, 'SQL study metadata'),
        manifest.ExportAction(file_list, 'export study metadata', 'export:meta'),
    ]

def make() -> list[Path]:
    return [manifest.save_actions_toml(make_actions(), 'study_meta.toml')]

if __name__ == '__main__':
    for target in make():
        print(target)
