# study prefix is the schema "root" or "tablespace" for tables in this study.
#
# TEMPLATE NOTE: set this to your study prefix and keep it identical to
# `study_prefix` in manifest.toml. These are two places today (a known
# refactor: tablespace.py could read manifest.py, but that currently creates a
# circular import). Change BOTH when you rename your study.
PREFIX = 'example'

#-----------------------------------------------------------------------------
# naming conventions
#-----------------------------------------------------------------------------
def name_prefix(table: list | str) -> list | str:
    if isinstance(table, list):
        return [f'{PREFIX}__{table}' for table in sorted(set(table))]
    else:
        return f'{PREFIX}__{table}'

def name_suffix(name: str, suffix=None) -> str:
    return f'{name}_{suffix}' if suffix else name

def name_trim(table) -> str:
    simple = table
    for part in ['cohort_', 'cube_', 'valueset_', 'elastic_']:
        simple = simple.replace(part, '')
    return simple.replace(name_prefix(''), '')

def name_join(part: str, table: str) -> str:
    return name_prefix('_'.join([part, name_trim(table)]))

def name_sample(table: str, suffix=None) -> str:
    part = name_suffix('sample', suffix)
    return name_join(part, table)

def name_cohort(table: str, suffix=None) -> str:
    part = name_suffix('cohort', suffix)
    return name_join(part, table)

def name_elastic(table: str, suffix=None) -> str:
    part = name_suffix('elastic', suffix)
    return name_join(part, table)

def name_encounter(suffix=None) -> str:
    return name_prefix(name_suffix('encounter', suffix))

def name_cube(table: str, suffix: str = None) -> str:
    part = f'cube_{suffix}' if suffix else 'cube'
    return name_join(part, table)

def name_valueset(table: str, suffix=None) -> str:
    part = f'valueset_{suffix}' if suffix else 'valueset'
    return name_join(part, table)

#-----------------------------------------------------------------------------
# Basic SQL to replace with JINJA Templates
#-----------------------------------------------------------------------------
def sql_list(clauses_list) -> str:
    return sql_iter(clauses_list, ',')

def sql_and(clauses_list) -> str:
    return sql_iter(clauses_list, 'and')

def sql_iter(clauses_list, operator=',') -> str:
    if not isinstance(clauses_list, list):
        return sql_iter([clauses_list])
    return f' {operator} \n'.join(sorted(list(set(clauses_list))))

def sql_quote(expression:str | list[str], quote="'", seperator=',') -> str:
    if not isinstance(expression, list):
        expression = [expression]
    expression = [f"{quote}{item}{quote}" for item in expression]
    return f'\n{seperator}'.join(expression)

#-----------------------------------------------------------------------------
# CTAS (create table as)
#-----------------------------------------------------------------------------
def ctas(source: str, variable: str, where: list) -> str:
    """
    CTAS(create table as) creates a COHORT table by selecting valueset matches
    from an encounter evidence table.
    """
    from_list = sql_list([source, name_valueset(variable)])
    cohort_name = name_cohort(variable)
    select = f"select distinct * from \n {from_list}"
    sql = [f'create table {cohort_name} as ',
           select, 'WHERE', sql_and(where)]
    return '\n'.join(sql)

def ctas_as_view(sql:str, table_name:str) -> str:
    create_table = f'CREATE TABLE {table_name} AS ('
    replace_view = f'CREATE or replace VIEW {table_name} AS '
    return sql.replace(create_table, replace_view).replace(');', ';')
