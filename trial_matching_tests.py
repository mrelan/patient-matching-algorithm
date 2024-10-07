import unittest
from datetime import datetime
from matching_algorithm import convert_age_to_months, calculate_patient_age, extract_age_from_criteria, process_criteria_with_nlp, match_patient_to_trial


# Unit Tests for convert_age_to_months
class TestConvertAgeToMonths(unittest.TestCase):
    def test_convert_years_to_months(self):
        self.assertEqual(convert_age_to_months("18 Years"), 18 * 12)

    def test_convert_months(self):
        self.assertEqual(convert_age_to_months("6 Months"), 6)

    def test_invalid_age(self):
        self.assertIsNone(convert_age_to_months(None))
        self.assertIsNone(convert_age_to_months(""))



# Unit Tests for calculate_patient_age()
class TestCalculatePatientAge(unittest.TestCase):
    def test_patient_age_in_months(self):
        # Assuming the patient was born on '2000-01-01', and the current year is 2024
        self.assertEqual(calculate_patient_age('2000-01-01'), (2024 - 2000) * 12)

# Unit Tests for extract_age_from_criteria()
class TestExtractAgeFromCriteria(unittest.TestCase):
    def test_extract_minimum_age(self):
        criteria_text = "Age >= 18 years"
        self.assertEqual(extract_age_from_criteria(criteria_text, age_type="minimum"), 18 * 12)

    def test_extract_maximum_age(self):
        criteria_text = "Age <= 65 years"
        self.assertEqual(extract_age_from_criteria(criteria_text, age_type="maximum"), 65 * 12)

    def test_no_age_found(self):
        criteria_text = "No age limit mentioned"
        self.assertIsNone(extract_age_from_criteria(criteria_text, age_type="minimum"))


# Unit Tests for process_criteria_with_nlp()
class TestProcessCriteriaWithNLP(unittest.TestCase):
    @patch('matching_algorithm.nlp')
    def test_process_inclusion_criteria(self, mock_nlp):
        # Mocking the NLP processing for a simple disease entity
        mock_doc = MagicMock()
        mock_doc.ents = [MagicMock(text='hypothyroidism', label_='DISEASE')]
        mock_nlp.return_value = mock_doc

        criteria_text = "INCLUSION CRITERIA: Hypothyroidism patients"
        result = process_criteria_with_nlp(criteria_text)

        self.assertEqual(result['inclusion']['conditions'], ['hypothyroidism'])

    @patch('matching_algorithm.nlp')
    def test_process_exclusion_criteria(self, mock_nlp):
        # Mocking the NLP processing for exclusion criteria
        mock_doc = MagicMock()
        mock_doc.ents = [MagicMock(text='anemia', label_='DISEASE')]
        mock_nlp.return_value = mock_doc

        criteria_text = "EXCLUSION CRITERIA: Anemia patients"
        result = process_criteria_with_nlp(criteria_text)

        self.assertEqual(result['exclusion']['conditions'], ['anemia'])


# Unit Tests for match_patient_to_trial()
class TestMatchPatientToTrial(unittest.TestCase):
    def setUp(self):
        self.patient_data = {
            'entry': [{
                'resource': {
                    'birthDate': '1990-01-01',
                    'resourceType': 'Condition',
                    'code': {'coding': [{'display': 'hypothyroidism'}]}
                }
            }]
        }
        self.trial_criteria = {
            'inclusion': {'conditions': ['hypothyroidism']},
            'exclusion': {'conditions': ['diabetes']},
            'trialId': 'NCT00001159',
            'trialName': 'Hypothyroidism Study'
        }

    def test_patient_eligible(self):
        result = match_patient_to_trial(self.patient_data, self.trial_criteria, 18 * 12, 65 * 12)
        self.assertIsNotNone(result)
        self.assertEqual(result['trialId'], 'NCT00001159')
        self.assertEqual(result['eligibilityCriteriaMet'], ['hypothyroidism'])

    def test_patient_ineligible_due_to_age(self):
        result = match_patient_to_trial(self.patient_data, self.trial_criteria, 30 * 12, 40 * 12)
        self.assertFalse(result)

    def test_patient_ineligible_due_to_exclusion(self):
        self.patient_data['entry'][0]['resource']['code']['coding'][0]['display'] = 'diabetes'
        result = match_patient_to_trial(self.patient_data, self.trial_criteria, 18 * 12, 65 * 12)
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()