import unittest
from unittest.mock import patch, MagicMock

from src import models, api_v1
from src.api_v1 import app

INSTRUMENT_ID = 1
INSTRUMENT_NAME = 'test_instrument'


class TestGalaxiesEndpointSetup(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Set up a test client for the application
        cls.client = app.test_client()
        # Set a valid token for authentication in tests
        cls.valid_token = 'valid_token'

    def setUp(self):
        # Mock the dump_json function to avoid actual JSON dumping during tests
        api_v1.dump_json = MagicMock()

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


class TestRemoveEventGalaxiesEndpoint(TestGalaxiesEndpointSetup):

    @patch('src.api_v1.db')
    def test_valid_listid_deletes_galaxy_list(self, mock_db):
        mock_db.session.query().filter().first.side_effect = [self.user, self.galaxy_list]
        response = self.client.post('/api/v1/remove_event_galaxies',
                                    json={'listid': self.galaxy_list.id, 'api_token': self.valid_token},
                                    headers={'Authorization': f'Bearer {self.valid_token}'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.decode(), 'Successfully deleted your galaxy list')

    @patch('src.api_v1.db')
    def test_invalid_listid_returns_error(self, mock_db):
        response = self.client.post('/api/v1/remove_event_galaxies',
                                    json={'listid': 'invalid', 'api_token': self.valid_token},
                                    headers={'Authorization': f'Bearer {self.valid_token}'})
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data.decode(), 'Invalid listid')

    @patch('src.api_v1.db')
    def test_missing_listid_returns_error(self, mock_db):
        response = self.client.post('/api/v1/remove_event_galaxies', json={'api_token': self.valid_token},
                                    headers={'Authorization': f'Bearer {self.valid_token}'})
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data.decode(), 'Event galaxy listid is required')

    @patch('src.api_v1.db')
    def test_unauthorized_user_returns_error(self, mock_db):
        self.galaxy_list.submitterid = 9999
        mock_db.session.query().filter().first.side_effect = [self.user, self.galaxy_list]
        response = self.client.post('/api/v1/remove_event_galaxies',
                                    json={'listid': self.galaxy_list.id, 'api_token': self.valid_token},
                                    headers={'Authorization': f'Bearer {self.valid_token}'})
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data.decode(),
                         'You can only delete information related to your api_token! shame shame')

    @patch('src.api_v1.db')
    def test_non_existent_listid_returns_error(self, mock_db):
        mock_db.session.query().filter().first.side_effect = [self.user, None]
        response = self.client.post('/api/v1/remove_event_galaxies',
                                    json={'listid': 9999, 'api_token': self.valid_token},
                                    headers={'Authorization': f'Bearer {self.valid_token}'})
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data.decode(), 'No galaxies with that listid')


class TestEventGalaxiesGetEndpoint(TestGalaxiesEndpointSetup):

    @patch('src.api_v1.db')
    def test_valid_graceid_returns_galaxy_entries(self, mock_db):
        models.db = mock_db
        mock_db.session.query().filter().all.side_effect = [self.mock_gw_alert, self.galaxy_entry]
        response = self.client.get('/api/v1/event_galaxies?graceid=valid_graceid&api_token=token',
                                   headers={'Authorization': f'Bearer {self.valid_token}'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.is_json)

    @patch('src.api_v1.db')
    def test_invalid_timesent_stamp_returns_error(self, mock_db):
        models.db = mock_db
        response = self.client.get(
            '/api/v1/event_galaxies?graceid=valid_graceid&timesent_stamp=invalid&api_token=token',
            headers={'Authorization': f'Bearer {self.valid_token}'})
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data.decode(),
                         "Error parsing date. Should be %Y-%m-%dT%H:%M:%S.%f format. e.g. 2019-05-01T12:00:00.00")

    @patch('src.api_v1.db')
    def test_valid_timesent_stamp_returns_galaxy_entries(self, mock_db):
        models.db = mock_db
        mock_db.session.query().filter().all.side_effect = [self.mock_gw_alert, self.galaxy_entry]
        response = self.client.get(
            '/api/v1/event_galaxies?graceid=valid_graceid&timesent_stamp=2019-05-01T12:00:00.00&api_token=token',
            headers={'Authorization': f'Bearer {self.valid_token}'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.is_json)

    @patch('src.api_v1.db')
    def test_invalid_listid_returns_error(self, mock_db):
        models.db = mock_db
        response = self.client.get('/api/v1/event_galaxies?graceid=valid_graceid&listid=invalid&api_token=token',
                                   headers={'Authorization': f'Bearer {self.valid_token}'})
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data.decode(), 'Invalid \'listid\'')

    @patch('src.api_v1.db')
    def test_valid_listid_returns_galaxy_entries(self, mock_db):
        models.db = mock_db
        mock_db.session.query().filter().all.side_effect = [self.mock_gw_alert, self.galaxy_entry]
        response = self.client.get('/api/v1/event_galaxies?graceid=valid_graceid&listid=1&api_token=token',
                                   headers={'Authorization': f'Bearer {self.valid_token}'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.is_json)

    @patch('src.api_v1.db')
    def test_valid_groupname_returns_galaxy_entries(self, mock_db):
        models.db = mock_db
        mock_db.session.query().filter().all.side_effect = [self.mock_gw_alert, self.galaxy_entry]
        response = self.client.get('/api/v1/event_galaxies?graceid=valid_graceid&groupname=test_group&api_token=token',
                                   headers={'Authorization': f'Bearer {self.valid_token}'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.is_json)

    @patch('src.api_v1.db')
    def test_valid_score_gt_returns_galaxy_entries(self, mock_db):
        models.db = mock_db
        mock_db.session.query().filter().all.side_effect = [self.mock_gw_alert, self.galaxy_entry]
        response = self.client.get('/api/v1/event_galaxies?graceid=valid_graceid&score_gt=0.5&api_token=token',
                                   headers={'Authorization': f'Bearer {self.valid_token}'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.is_json)

    @patch('src.api_v1.db')
    def test_valid_score_lt_returns_galaxy_entries(self, mock_db):
        models.db = mock_db
        mock_db.session.query().filter().all.side_effect = [self.mock_gw_alert, self.galaxy_entry]
        response = self.client.get('/api/v1/event_galaxies?graceid=valid_graceid&score_lt=1.5&api_token=token',
                                   headers={'Authorization': f'Bearer {self.valid_token}'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.is_json)


class TestEventGalaxiesPostEndpoint(TestGalaxiesEndpointSetup):

    @patch('src.api_v1.db')
    def test_post_event_galaxies_v1_valid_request(self, mock_db):
        models.db = mock_db
        mock_db.session.query().filter().all.return_value = [MagicMock()]
        response = self.client.post('/api/v1/event_galaxies', json={
            'api_token': 'token',
            'graceid': 'valid_graceid',
            'timesent_stamp': self.valid_timesent_stamp,
            'galaxies': self.valid_galaxies
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('Successful adding of', response.data.decode())

    @patch('src.api_v1.db')
    def test_post_event_galaxies_v1_invalid_api_token(self, mock_db):
        models.db = mock_db
        mock_db.session.query(models.users).filter(models.users.api_token == 'invalid').first.return_value = None
        response = self.client.post('/api/v1/event_galaxies', json={
            'api_token': 'invalid',
            'graceid': 'valid_graceid',
            'timesent_stamp': self.valid_timesent_stamp,
            'galaxies': self.valid_galaxies
        })
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data.decode(), 'invalid api_token')

    @patch('src.api_v1.db')
    def test_post_event_galaxies_v1_missing_api_token(self, mock_db):
        models.db = mock_db
        response = self.client.post('/api/v1/event_galaxies', json={
            'graceid': 'valid_graceid',
            'timesent_stamp': self.valid_timesent_stamp,
            'galaxies': self.valid_galaxies
        })
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data.decode(), 'api_token is required')

    @patch('src.api_v1.db')
    def test_post_event_galaxies_v1_invalid_graceid(self, mock_db):
        models.db = mock_db
        response = self.client.post('/api/v1/event_galaxies', json={
            'api_token': 'valid_api_token',
            'graceid': 'invalid_graceid',
            'timesent_stamp': self.valid_timesent_stamp,
            'galaxies': self.valid_galaxies
        })
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data.decode(), 'Invalid graceid')

    @patch('src.api_v1.db')
    def test_post_event_galaxies_v1_missing_graceid(self, mock_db):
        models.db = mock_db
        response = self.client.post('/api/v1/event_galaxies', json={
            'api_token': 'valid_api_token',
            'timesent_stamp': self.valid_timesent_stamp,
            'galaxies': self.valid_galaxies
        })
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data.decode(), 'graceid is required')

    @patch('src.api_v1.db')
    def test_post_event_galaxies_v1_invalid_timesent_stamp(self, mock_db):
        models.db = mock_db
        mock_db.session.query(models.users).filter().first.return_value = MagicMock()
        mock_db.session.query().filter().all.return_value = [MagicMock()]
        response = self.client.post('/api/v1/event_galaxies', json={
            'api_token': 'valid_api_token',
            'graceid': 'valid_graceid',
            'timesent_stamp': 'not a timestamp',
            'galaxies': self.valid_galaxies
        })
        self.assertEqual(response.status_code, 500)
        self.assertIn('Error parsing date', response.data.decode())

    @patch('src.api_v1.db')
    def test_post_event_galaxies_v1_missing_timesent_stamp(self, mock_db):
        models.db = mock_db
        mock_db.session.query(models.users).filter().first.return_value = MagicMock()
        mock_db.session.query().filter().all.return_value = [MagicMock()]
        response = self.client.post('/api/v1/event_galaxies', json={
            'api_token': 'valid_api_token',
            'graceid': 'valid_graceid',
            'galaxies': self.valid_galaxies
        })
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data.decode(), 'timesent_stamp is required')

    @patch('src.api_v1.db')
    def test_post_event_galaxies_v1_missing_galaxies(self, mock_db):
        models.db = mock_db
        mock_db.session.query(models.users).filter().first.return_value = MagicMock()
        mock_db.session.query().filter().all.return_value = [MagicMock()]
        response = self.client.post('/api/v1/event_galaxies', json={
            'api_token': 'valid_api_token',
            'graceid': 'valid_graceid',
            'timesent_stamp': self.valid_timesent_stamp
        })
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data.decode(), 'a list of galaxies is required')


if __name__ == '__main__':
    unittest.main()
