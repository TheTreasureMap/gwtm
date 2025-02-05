import unittest
from unittest.mock import patch, MagicMock

from src import models, api_v1
from src.api_v1 import app


class AlertsEndpointSetup(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Set up a test client for the application
        cls.client = app.test_client()
        # Set a valid token for authentication in tests
        cls.valid_token = 'valid_token'


class TestAlertsGetEndpoint(AlertsEndpointSetup):

    @patch('src.api_v1.initial_request_parse')
    @patch('src.api_v1.db')
    def test_query_alerts_success(self, mock_db, mock_initial_request_parse):
        models.db = mock_db
        # Mock the initial_request_parse to return valid data
        mock_initial_request_parse.return_value = (True, '', {'graceid': 'S190425z'}, MagicMock())

        # Mock the database query
        mock_alert = MagicMock(
            parse={'graceid': 'S190425z', 'alert_type': 'Initial'})
        mock_db.session.query.filter.order_by.all.retrun_value = [mock_alert]

        response = self.client.get('/api/v1/query_alerts', query_string={'graceid': 'S190425z'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.is_json, True)

    @patch('src.api_v1.initial_request_parse')
    @patch('src.api_v1.db')
    def test_query_alerts_invalid_request(self, mock_db, mock_initial_request_parse):
        models.db = mock_db
        # Mock the initial_request_parse to return invalid data
        mock_initial_request_parse.return_value = (False, 'Invalid request', {}, None)

        response = self.client.get('/api/v1/query_alerts')

        self.assertEqual(response.status_code, 500)
        self.assertIn('Invalid request', response.data.decode('utf-8'))


class TestAlertsPostEndpoint(AlertsEndpointSetup):

    @patch('src.api_v1.initial_request_parse')
    @patch('src.api_v1.db')
    def test_post_alert_success(self, mock_db, mock_initial_request_parse):
        # Mock the initial_request_parse to return valid data
        mock_initial_request_parse.return_value = (True, '', {'graceid': 'S190425z'}, MagicMock(id=2))

        # Mock the database session
        mock_alert = MagicMock()
        mock_alert.parse = {'graceid': 'S190425z', 'alert_type': 'Initial'}
        mock_db.session.add.return_value = None
        mock_db.session.flush.return_value = None
        mock_db.session.commit.return_value = None

        response = self.client.post('/api/v1/post_alert', json={'graceid': 'S190425z'})

        self.assertEqual(response.status_code, 200)
        self.assertIn('S190425z', response.data.decode('utf-8'))


    @patch('src.api_v1.initial_request_parse')
    @patch('src.api_v1.db')
    def test_post_alert_invalid_request(self, mock_db, mock_initial_request_parse):
        # Mock the initial_request_parse to return invalid data
        mock_initial_request_parse.return_value = (False, 'Invalid request', {}, None)

        response = self.client.post('/api/v1/post_alert')

        self.assertEqual(response.status_code, 500)
        self.assertIn('Invalid request', response.data.decode('utf-8'))

    @patch('src.api_v1.initial_request_parse')
    @patch('src.api_v1.db')
    def test_post_alert_unauthorized_user(self, mock_db, mock_initial_request_parse):
        # Mock the initial_request_parse to return a non-admin user
        mock_initial_request_parse.return_value = (True, '', {'graceid': 'S190425z'}, MagicMock(id=1))

        response = self.client.post('/api/v1/post_alert', json={'graceid': 'S190425z'})

        self.assertEqual(response.status_code, 500)
        self.assertIn('Only admin can access this endpoint', response.data.decode('utf-8'))




if __name__ == '__main__':
    unittest.main()
