import unittest
from unittest.mock import patch, MagicMock

from src import api_v1
from src.api_v1 import app, initial_request_parse, make_response

INSTRUMENT_ID = 1
INSTRUMENT_NAME = 'test_instrument'
FOOTPRINT = 'test footprint'


class TestFootprintEndpointSetup(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Set up a test client for the application
        cls.client = app.test_client()
        # Set a valid token for authentication in tests
        cls.valid_token = 'valid_token'

    def setUp(self):
        # Mock the dump_json function to avoid actual JSON dumping during tests
        api_v1.dump_json = MagicMock()

        # Mock footprint object with parsed data
        self.footprint = MagicMock(
            parse={'instrumentid': INSTRUMENT_ID, 'name': INSTRUMENT_NAME, 'footprint': FOOTPRINT})


class TestFootprintGetEndpoint(TestFootprintEndpointSetup):

    @patch('src.api_v1.db')
    def test_valid_request_returns_footprints(self, mock_db):
        response = self.client.get('/api/v1/footprints?api_token=token',
                                   headers={'Authorization': f'Bearer {self.valid_token}'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.is_json, True)

    @patch('src.api_v1.db')
    def test_invalid_request_returns_error(self, mock_db):
        response = self.client.get('/api/v1/footprints')
        self.assertEqual(response.status_code, 500)

    @patch('src.api_v1.db')
    def test_valid_id_returns_correct_footprint(self, mock_db):
        mock_db.session.query().filter().all.return_value = [self.footprint]
        response = self.client.get(f'/api/v1/footprints?id={self.footprint.instrumentid}&api_token=token',
                                   headers={'Authorization': f'Bearer {self.valid_token}'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json), 1)
        self.assertEqual(response.json[0]['instrumentid'], INSTRUMENT_ID)

    @patch('src.api_v1.db')
    def test_valid_name_returns_correct_footprint(self, mock_db):
        mock_db.session.query().filter().all.return_value = [self.footprint]
        response = self.client.get(f'/api/v1/footprints?name={INSTRUMENT_NAME}&api_token=token',
                                   headers={'Authorization': f'Bearer {self.valid_token}'})
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.json), 0)
        self.assertTrue(any(fp['instrumentid'] == INSTRUMENT_ID for fp in response.json))

    @patch('src.api_v1.db')
    def test_invalid_id_returns_empty_list(self, mock_db):
        response = self.client.get('/api/v1/footprints?id=9999&api_token=token',
                                   headers={'Authorization': f'Bearer {self.valid_token}'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json), 0)

    @patch('src.api_v1.db')
    def test_invalid_name_returns_empty_list(self, mock_db):
        response = self.client.get('/api/v1/footprints?name=nonexistent&api_token=token',
                                   headers={'Authorization': f'Bearer {self.valid_token}'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json), 0)


if __name__ == '__main__':
    unittest.main()