import unittest
from datetime import datetime
from unittest.mock import patch, MagicMock

from src import models, api_v1
from src.api_v1 import app
from src.enums import pointing_status, depth_unit, bandpass
from src.models import instrument, gw_alert

INSTRUMENT_ID = 1
INSTRUMENT_NAME = 'test_instrument'
FOOTPRINT = 'test footprint'


def define_mock_pointing():
    # Create a mock pointing object
    mock_pointing = {
        "status": pointing_status.completed,
        "instrumentid": '1',
        "position": "POINT(1 1)",
        "galaxy_catalog": 123,
        "galaxy_catalogid": 456,
        "depth": 20.5,
        "depth_err": 0.5,
        "depth_unit": depth_unit.ab_mag,
        "time": datetime.now().isoformat(),
        "datecreated": datetime.now().isoformat(),
        "dateupdated": datetime.now().isoformat(),
        "submitterid": 1234,
        "pos_angle": 45.0,
        "band": bandpass.U,
        "central_wave": 500.0,
        "bandwidth": 50.0
    }

    return mock_pointing


class TestPointingsSetup(unittest.TestCase):

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
        # Mock user object with an ID
        self.user = MagicMock(id=1234)
        # Mock galaxy list object with an ID and submitter ID
        self.galaxy_list = MagicMock(id=1, submitterid=1234)
        # Mock GW alert object with a graceid
        self.mock_gw_alert = MagicMock(graceid='graceid')
        # Set a valid timestamp for timesent
        self.valid_timesent_stamp = '2019-05-01T12:00:00.00'
        # Mock valid galaxies data
        self.valid_galaxies = [
            {'ra': 0.0, 'dec': 0.0, 'score': 0.0, 'name': 'test_name', 'rank': 123, 'groupname': 'test_group'}]
        # Mock galaxy entry object
        self.galaxy_entry = [MagicMock()]
        # Mock valid candidate data
        self.valid_candidate_data = MagicMock(id='valid_candidate_id')


class TestPointingsPostEndpoint(TestPointingsSetup):

    @patch('src.api_v1.db')
    def test_add_pointings_v1_valid_request(self, mock_db):
        models.db = mock_db
        mock_db.session.query().filter().all.return_value = [MagicMock()]  # mock for graceid
        mock_db.session.query(models.instrument.instrument_name, models.instrument.id).all.return_value = [
            instrument(id=1)]
        valid_pointings = [define_mock_pointing()]
        response = self.client.post('/api/v1/pointings', json={
            'api_token': 'valid_api_token',
            'graceid': 'valid_graceid',
            'pointings': valid_pointings
        })
        assert response.status_code == 200
        assert len(response.json['pointing_ids']) == len(valid_pointings)

    @patch('src.api_v1.db')
    def test_add_pointings_v1_invalid_grace_id(self, mock_db):
        models.db = mock_db
        mock_db.session.query().filter().all.side_effect = [[gw_alert(graceid='invalid', alternateid='invalid')],
                                                            []]  # mock for graceid
        response = self.client.post('/api/v1/pointings', json={
            'api_token': 'valid_api_token',
            'graceid': 'valid_graceid',
            'pointings': [define_mock_pointing()]
        })
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data.decode(), 'Invalid graceid')

    @patch('src.api_v1.db')
    def test_add_pointings_v1_missing_api_token(self, mock_db):
        valid_pointings = [define_mock_pointing()]
        response = self.client.post('/api/v1/pointings', json={
            'graceid': "valid_graceid",
            'pointings': valid_pointings
        })
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data.decode(), 'api_token is required')

    @patch('src.api_v1.db')
    def test_add_pointings_v1_invalid_api_token(self, mock_db):
        apitoken = 'invalid_api_token'
        mock_db.session.query(models.users).filter(
            models.users.api_token == 'invalid_api_token').first.return_value = None
        response = self.client.post('/api/v1/pointings', json={
            'api_token': apitoken,
            'graceid': 'valid_graceid',
            'pointings': define_mock_pointing()
        })
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data.decode(), 'Invalid api_token')

    @patch('src.api_v1.db')
    def test_add_pointings_v1_missing_graceid(self, mock_db):
        response = self.client.post('/api/v1/pointings', json={
            'api_token': 'valid_api_token',
            'pointings': define_mock_pointing()
        })
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data.decode(), 'graceid is required')

    @patch('src.api_v1.db')
    def test_add_pointings_v1_missing_pointings_format(self, mock_db):
        models.db = mock_db
        mock_db.session.query().filter().all.return_value = [MagicMock()]  # mock for graceid
        response = self.client.post('/api/v1/pointings', json={
            'api_token': 'valid_api_token',
            'graceid': 'valid_graceid',
        })
        self.assertEqual(response.status_code, 500)
        self.assertTrue('Invalid request' in response.data.decode())


class TestPointingsGetEndpoint(TestPointingsSetup):

    @patch('src.api_v1.db')
    def test_get_pointings_v1_valid_request(self, mock_db):
        models.db = mock_db
        mock_db.session.query(models.users).filter().first.return_value = MagicMock()
        mock_db.session.query().filter().all.return_value = [MagicMock()]
        response = self.client.get('/api/v1/pointings', query_string={
            'api_token': 'valid_api_token',
            'graceid': 'valid_graceid'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.is_json)

    @patch('src.api_v1.db')
    def test_get_pointings_v1_invalid_api_token(self, mock_db):
        mock_db.session.query(models.users).filter().first.return_value = None  # mock for invalid api_token
        response = self.client.get('/api/v1/pointings', query_string={
            'api_token': 'invalid_api_token',
            'graceid': 'valid_graceid'
        })
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data.decode(), 'Invalid api_token')

    @patch('src.api_v1.db')
    def test_get_pointings_v1_missing_api_token(self, mock_db):
        response = self.client.get('/api/v1/pointings', query_string={
            'graceid': 'valid_graceid'
        })
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data.decode(), 'api_token is required')


if __name__ == '__main__':
    unittest.main()
