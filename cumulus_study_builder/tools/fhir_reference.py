from enum import Enum

#-----------------------------------------------------------------------------
# Aspects
#-----------------------------------------------------------------------------
class Aspect(Enum):
    """
    Aspect is the type of healthcare concept.
    Aspect name is the short key or alias; Aspect value is the FHIR resource.
    https://docs.smarthealthit.org/cumulus/library/core-study-details.html
    """
    enc = 'encounter'
    dx = 'condition'
    rx = 'medicationrequest'
    lab = 'observation_lab'
    proc = 'procedure'
    doc = 'documentreference'
    diag = 'diagnosticreport'
    allergy = 'allergy'

def list_aspect() -> list[str]:
    return [aspect.name for aspect in Aspect]

def get_aspect(variable_name:str) -> Aspect:
    return Aspect[variable_name.split('_')[0]]

#-----------------------------------------------------------------------------
# Column
#-----------------------------------------------------------------------------
class Column:
    def __init__(self, code:str=None, system:str=None, aspect=None, resource:str=None, reference:str=None):
        if not aspect:
            aspect = get_aspect(code)
        if isinstance(aspect, str):
            aspect = get_aspect(aspect)
        if not resource:
            resource = aspect.value
        if not reference:
            reference = f"{resource}_ref"
        self.code = code
        self.aspect = aspect
        self.system = system
        self.resource = resource
        self.reference = reference

    def __dict__(self) -> dict:
        return {'code':self.code, 'system': self.system, 'aspect': self.aspect.name,
                'resource': self.resource, 'reference': self.reference}

    def __str__(self):
        return str(self.__dict__())

def get_column(variable_name:str) -> Column:
    """
    Get column metadata for a given variable name. Returns the longest match.
    """
    match_list = [col.name for col in ColumnEnum if variable_name.startswith(col.name)]
    best_match = max(match_list, key=len)
    return ColumnEnum[best_match].value

#-----------------------------------------------------------------------------
# Column Enum : known supported column types
#-----------------------------------------------------------------------------
class ColumnEnum(Enum):
    diag = Column('diag_code', 'diag_system')
    diag_category = Column('diag_category_code','diag_category_system')
    diag_conclusion = Column('diag_conclusioncode_code','diag_conclusioncode_system')
    doc = Column('doc_type_code', 'doc_type_system')
    dx = Column('dx_code', 'dx_system')
    dx_category = Column('dx_category_code','dx_category_system')
    enc = Column('enc_type_code', 'enc_type_system')
    enc_class = Column('enc_class_code', 'enc_class_system')
    enc_type = Column('enc_type_code', 'enc_type_system')
    enc_servicetype = Column('enc_servicetype_code','enc_servicetype_system')
    enc_priority = Column('enc_priority_code', 'enc_priority_system')
    enc_dischargedisposition = Column('enc_dischargedisposition_code', 'enc_dischargedisposition_system')
    lab = Column('lab_observation_code', 'lab_observation_system', 'lab', 'observation_lab', 'observation_ref')
    lab_interpretation = Column('lab_interpretation_code','lab_interpretation_system')
    proc = Column('proc_code', 'proc_system')
    proc_category = Column('proc_category_code','proc_category_system')
    rx = Column('rx_code', 'rx_system')
    rx_category = Column('rx_category_code','rx_category_system')
