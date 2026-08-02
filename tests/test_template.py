import unittest
from cumulus_study_builder.tools import template, tablespace
from cumulus_study_builder.tools.settings import ENCOUNTER_REF

class TestTemplate(unittest.TestCase):
    def test_prefix(self):
        # Prefix-agnostic: assert the template renders with the CONFIGURED study
        # prefix (tablespace.PREFIX), so the test passes after a user sets their own
        # prefix rather than hardcoding the shipped 'example'.
        file = 'cohort_study_period.sql'
        text = template.load(file)
        self.assertTrue(f'{tablespace.PREFIX}__cohort_study_period' in text)

    def test_study_encounter_renders(self):
        # Renders without error and asserts the base encounter grain contract.
        text = template.load('encounter.sql')
        self.assertIn(f'{tablespace.PREFIX}__encounter AS', text)
        self.assertIn('PARTITION BY encounter_ref', text)
        self.assertIn('encounter_row_num = 1', text)
        self.assertIn('enc.encounter_ref IS NOT NULL', text)
        self.assertNotIn('enc_servicetype_code', text)
        self.assertEqual(
            f'{tablespace.PREFIX}__encounter_dx',
            tablespace.name_encounter('dx'),
        )

    # NOTE: the source study also tests aspect + sample templates
    # (encounter_dx.sql, sample_casedef_temporality.sql). Those
    # templates are copied from your source study on sync; re-enable then.
