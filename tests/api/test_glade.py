import unittest
from unittest.mock import patch, MagicMock

from src import api_v1
from src.api_v1 import app


class TestGladeEndpointSetup(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Set up a test client for the application
        cls.client = app.test_client()
        # Set a valid token for authentication in tests
        cls.valid_token = 'valid_token'

    def setUp(self):
        # Mock user object with an ID
        self.user = MagicMock(id=1234)


class TestGladeGetEndpoint(TestGladeEndpointSetup):

    @patch('src.api_v1.initial_request_parse')
    @patch('src.api_v1.db.session.query')
    def test_valid_request(self, mock_query, mock_initial_request_parse):
        mock_initial_request_parse.return_value = (True, '', {'ra': '10.0', 'dec': '20.0'}, MagicMock())
        mock_query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []

        response = self.client.get('/api/v1/glade')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.is_json, True)

    @patch('src.api_v1.initial_request_parse')
    def test_invalid_request(self, mock_initial_request_parse):
        mock_initial_request_parse.return_value = (False, 'Invalid request', None, None)

        response = self.client.get('/api/v1/glade')

        self.assertEqual(response.status_code, 500)
        self.assertIn('Invalid request', response.data.decode())

    @patch('src.api_v1.initial_request_parse')
    def test_initial_request_parsing_failure(self, mock_initial_request_parse):
        mock_initial_request_parse.return_value = (False, 'Invalid Arguments.', None, None)

        response = self.client.get('/api/v1/glade')

        self.assertEqual(response.status_code, 500)
        self.assertIn('Invalid Arguments.', response.data.decode())

    @patch('src.api_v1.initial_request_parse')
    @patch('src.api_v1.db.session.query')
    def test_valid_ra_dec_parameters(self, mock_query, mock_initial_request_parse):
        mock_initial_request_parse.return_value = (True, '', {'ra': '10.0', 'dec': '20.0'}, MagicMock())
        mock_query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []

        response = self.client.get('/api/v1/glade')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.is_json, True)

    @patch('src.api_v1.initial_request_parse')
    @patch('src.api_v1.db.session.query')
    def test_filtering_by_name(self, mock_query, mock_initial_request_parse):
        mock_initial_request_parse.return_value = (True, '', {'name': 'Andromeda'}, MagicMock())
        mock_query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []

        response = self.client.get('/api/v1/glade')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.is_json, True)

    @patch('src.api_v1.initial_request_parse')
    @patch('src.api_v1.db.session.query')
    def test_filtering_and_ordering(self, mock_query, mock_initial_request_parse):
        mock_initial_request_parse.return_value = (
        True, '', {'ra': '10.0', 'dec': '20.0', 'name': 'Andromeda'}, MagicMock())
        mock_query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []

        response = self.client.get('/api/v1/glade')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.is_json, True)

    @patch('src.api_v1.initial_request_parse')
    @patch('src.api_v1.db.session.query')
    def test_successful_retrieval(self, mock_query, mock_initial_request_parse):
        mock_initial_request_parse.return_value = (True, '', {}, MagicMock())
        mock_query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []

        response = self.client.get('/api/v1/glade')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, [])


if __name__ == '__main__':
    unittest.main()
