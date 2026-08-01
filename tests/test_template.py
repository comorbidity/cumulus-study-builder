import unittest
from cumulus_study_builder.tools import template
from cumulus_study_builder.tools.settings import ENCOUNTER_REF

class TestTemplate(unittest.TestCase):
    def test_prefix(self):
        file = 'cohort_study_period.sql'
        text = template.load(file)
        self.assertTrue('example__cohort_study_period' in text)

    def test_study_population_renders(self):
        # renders without error (requires the study_population templates present)
        template.load('cohort_study_population.sql')

    # NOTE: the source study also tests aspect + sample templates
    # (cohort_study_population_dx.sql, sample_casedef_temporality.sql). Those
    # templates are copied from your source study on sync; re-enable then.
