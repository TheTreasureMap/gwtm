import unittest
from unittest.mock import patch, MagicMock

from src.api_v1 import app


class TestDeleteCandidateEndpoint(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Set up a test client for the application
        cls.client = app.test_client()

    def setUp(self):
        # Common setup for each test
        self.mock_user = MagicMock()
        self.mock_user.id = 1
        self.mock_candidate = MagicMock()
        self.mock_candidate.submitterid = 1
        self.mock_candidate.id = 123

    @patch('src.api_v1.db')
    @patch('src.api_v1.initial_request_parse')
    def test_delete_single_valid_candidate(self, mock_initial_request_parse, mock_db):
        mock_initial_request_parse.return_value = (True, '', {'id': 123}, self.mock_user)
        mock_db.session.query.return_value.filter.return_value.first.return_value = self.mock_candidate

        response = self.client.delete('/api/v1/candidate', json={'id': 123})

        self.assertEqual(response.status_code, 200)
        self.assertIn('Successfully deleted 1 candidate(s)', response.data.decode())

    @patch('src.api_v1.db')
    @patch('src.api_v1.initial_request_parse')
    def test_delete_invalid_candidate_id(self, mock_initial_request_parse, mock_db):
        mock_initial_request_parse.return_value = (True, '', {'id': 999}, self.mock_user)
        mock_db.session.query.return_value.filter.return_value.first.return_value = None

        response = self.client.delete('/api/v1/candidate', json={'id': 999})

        self.assertEqual(response.status_code, 500)
        self.assertIn('No candidate found with', response.data.decode())

    @patch('src.api_v1.db')
    @patch('src.api_v1.initial_request_parse')
    def test_delete_multiple_valid_candidates(self, mock_initial_request_parse, mock_db):
        mock_candidate2 = MagicMock()
        mock_candidate2.submitterid = 1
        mock_candidate2.id = 124

        mock_initial_request_parse.return_value = (True, '', {'ids': [123, 124]}, self.mock_user)
        mock_db.session.query.return_value.filter.return_value.all.return_value = [self.mock_candidate, mock_candidate2]

        response = self.client.delete('/api/v1/candidate', json={'ids': [123, 124]})

        self.assertEqual(response.status_code, 200)
        self.assertIn('Successfully deleted 2 candidate(s)', response.data.decode())

    @patch('src.api_v1.initial_request_parse')
    def test_delete_invalid_ids_format(self, mock_initial_request_parse):
        mock_initial_request_parse.return_value = (True, '', {'ids': 'invalid_format'}, self.mock_user)

        response = self.client.delete('/api/v1/candidate', json={'ids': 'invalid_format'})

        self.assertEqual(response.status_code, 500)
        self.assertIn('Invalid \'ids\' format', response.data.decode())

    @patch('src.api_v1.db')
    @patch('src.api_v1.initial_request_parse')
    def test_unauthorized_single_candidate_deletion(self, mock_initial_request_parse, mock_db):
        self.mock_user.id = 2
        mock_initial_request_parse.return_value = (True, '', {'id': 123}, self.mock_user)
        mock_db.session.query.return_value.filter.return_value.first.return_value = self.mock_candidate

        response = self.client.delete('/api/v1/candidate', json={'id': 123})

        self.assertEqual(response.status_code, 500)
        self.assertIn('Error: Unauthorized', response.data.decode())

    @patch('src.api_v1.db')
    @patch('src.api_v1.initial_request_parse')
    def test_no_candidates_found_for_deletion(self, mock_initial_request_parse, mock_db):
        mock_initial_request_parse.return_value = (True, '', {'ids': [999, 1000]}, self.mock_user)
        mock_db.session.query.return_value.filter.return_value.all.return_value = []

        response = self.client.delete('/api/v1/candidate', json={'ids': [999, 1000]})

        self.assertEqual(response.status_code, 500)
        self.assertIn('No candidates found with input', response.data.decode())

    @patch('src.api_v1.initial_request_parse')
    def test_invalid_id_type(self, mock_initial_request_parse):
        mock_initial_request_parse.return_value = (True, '', {'id': 'invalid_type'}, self.mock_user)

        response = self.client.delete('/api/v1/candidate', json={'id': 'invalid_type'})

        self.assertEqual(response.status_code, 500)
        self.assertIn('Invalid candidate \'id\'', response.data.decode())

    @patch('src.api_v1.initial_request_parse')
    def test_invalid_ids_format_again(self, mock_initial_request_parse):
        mock_initial_request_parse.return_value = (True, '', {'ids': '[invalid]'}, self.mock_user)

        response = self.client.delete('/api/v1/candidate', json={'ids': '[invalid]'})

        self.assertEqual(response.status_code, 500)
        self.assertIn('Invalid \'ids\' format', response.data.decode())

    @patch('src.api_v1.db')
    @patch('src.api_v1.initial_request_parse')
    def test_successful_single_candidate_deletion(self, mock_initial_request_parse, mock_db):
        mock_initial_request_parse.return_value = (True, '', {'id': 123}, self.mock_user)
        mock_db.session.query.return_value.filter.return_value.first.return_value = self.mock_candidate

        response = self.client.delete('/api/v1/candidate', json={'id': 123})

        self.assertEqual(response.status_code, 200)
        self.assertIn('Successfully deleted 1 candidate(s)', response.data.decode())


if __name__ == '__main__':
    unittest.main()
