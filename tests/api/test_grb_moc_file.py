import unittest
from unittest.mock import patch, MagicMock

from src import models
from src.api_v1 import app


class TestGrbMocFileGetEndpoint(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Set up a test client for the application
        cls.client = app.test_client()

    @patch('src.api_v1.initial_request_parse')
    @patch('src.api_v1.db')
    def test_get_grbmoc_v1_valid_request(self, mock_db, mock_initial_request_parse):
        models.db = mock_db
        mock_initial_request_parse.return_value = (
            True, '', {'graceid': 'valid_graceid', 'instrument': 'gbm'}, MagicMock())
        mock_file = MagicMock()
        mock_file.read.return_value = b'file_content'
        mock_db.session.query().filter().all.return_value = [MagicMock()]
        with patch('src.api_v1.gwtm_io.download_gwtm_file', return_value=mock_file):
            response = self.client.get('/api/v1/grb_moc_file',
                                       query_string={'graceid': 'valid_graceid', 'instrument': 'gbm'})
            self.assertEqual(response.status_code, 200)

    @patch('src.api_v1.initial_request_parse')
    @patch('src.api_v1.db')
    def test_get_grbmoc_v1_invalid_graceid(self, mock_db, mock_initial_request_parse):
        models.db = mock_db
        mock_initial_request_parse.return_value = (True, '', {'instrument': 'gbm'}, MagicMock())
        response = self.client.get('/api/v1/grb_moc_file', query_string={'instrument': 'gbm'})
        self.assertEqual(response.status_code, 500)
        self.assertIn('graceid is required', response.data.decode())

    @patch('src.api_v1.initial_request_parse')
    @patch('src.api_v1.db')
    def test_get_grbmoc_v1_invalid_instrument(self, mock_db, mock_initial_request_parse):
        models.db = mock_db
        mock_initial_request_parse.return_value = (True, '', {'graceid': 'valid_graceid'}, MagicMock())
        response = self.client.get('/api/v1/grb_moc_file', query_string={'graceid': 'valid_graceid'})
        self.assertEqual(response.status_code, 500)
        self.assertIn('Instrument is required', response.data.decode())

    @patch('src.api_v1.initial_request_parse')
    @patch('src.api_v1.db')
    def test_get_grbmoc_v1_invalid_instrument_value(self, mock_db, mock_initial_request_parse):
        models.db = mock_db
        mock_initial_request_parse.return_value = (
            True, '', {'graceid': 'valid_graceid', 'instrument': 'invalid'}, MagicMock())
        response = self.client.get('/api/v1/grb_moc_file',
                                   query_string={'graceid': 'valid_graceid', 'instrument': 'invalid'})
        self.assertEqual(response.status_code, 500)
        self.assertIn('Valid instruments are in', response.data.decode())

    @patch('src.api_v1.initial_request_parse')
    @patch('src.api_v1.db')
    def test_get_grbmoc_v1_file_not_found(self, mock_db, mock_initial_request_parse):
        models.db = mock_db
        mock_initial_request_parse.return_value = (
            True, '', {'graceid': 'valid_graceid', 'instrument': 'gbm'}, MagicMock())
        mock_db.session.query().filter().all.return_value = [MagicMock()]
        with patch('src.api_v1.gwtm_io.download_gwtm_file', side_effect=Exception('File not found')):
            response = self.client.get('/api/v1/grb_moc_file',
                                       query_string={'graceid': 'valid_graceid', 'instrument': 'gbm'})
            self.assertEqual(response.status_code, 200)
            self.assertIn('MOC file for GW-Alert', response.data.decode())


if __name__ == '__main__':
    unittest.main()
