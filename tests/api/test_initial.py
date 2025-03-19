import unittest
from unittest.mock import patch, MagicMock

from src.api_v1 import initial_request_parse, make_response

class InitialRequestTests(unittest.TestCase):

    def setUp(self):
        self.mock_request = MagicMock()

    @patch('src.api_v1.db')
    def test_initial_request_parse_valid_json(self, mock_db):
        # Mock request object with valid JSON data
        self.mock_request.get_json.return_value = {'api_token': 'valid_token'}
        # Mock database query to return a valid user
        mock_db.session.query().filter().first.return_value = MagicMock()
        # Call the function to test with the mocked request
        valid, message, args, user = initial_request_parse(self.mock_request, only_json=True)
        # Assert that the function returns valid results
        self.assertTrue(valid)
        self.assertEqual(message, '')
        self.assertIsNotNone(args)
        self.assertIsNotNone(user)

    @patch('src.api_v1.db')
    def test_initial_request_parse_invalid_json(self, mock_db):
        self.mock_request.get_json.side_effect = Exception()
        # Call the function to test with the mocked request
        valid, message, args, user = initial_request_parse(self.mock_request, only_json=True)
        # Assert that the function returns invalid results
        self.assertFalse(valid)
        self.assertEqual(message, 'Endpoint only accepts json argument parameters')
        self.assertIsNone(args)
        self.assertIsNone(user)

    @patch('src.api_v1.db')
    def test_initial_request_parse_missing_token(self, mock_db):
        self.mock_request.get_json.return_value = {}
        valid, message, args, user = initial_request_parse(self.mock_request, only_json=True)
        self.assertFalse(valid)
        self.assertEqual(message, 'api_token is required')
        self.assertIsNotNone(args)
        self.assertIsNone(user)

    @patch('src.api_v1.db')
    def test_make_response_valid(self, mock_db):
        response = make_response('Success', 200)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.response, [b'Success'])

    @patch('src.api_v1.db')
    def test_make_response_invalid(self, mock_db):
        response = make_response('Error', 500)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.response, [b'Error'])