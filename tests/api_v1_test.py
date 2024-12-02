
import unittest
from unittest.mock import patch, MagicMock

from src import models, api_v1
from src.api_v1 import app, initial_request_parse, make_response

INSTRUMENT_ID = 1
INSTRUMENT_NAME = 'test_instrument'
FOOTPRINT = 'test footprint'

class ApiV1Tests(unittest.TestCase):


    @classmethod
    def setUpClass(self):
        self.client = app.test_client()
        self.valid_token = 'valid_token'

    def setUp(self):
        #json.dumps = MagicMock() # Mock json.dumps to avoid error
        api_v1.dump_json = MagicMock()
        self.footprint = MagicMock()
        self.footprint.parse = {'instrumentid': INSTRUMENT_ID, 'name': INSTRUMENT_NAME, 'footprint': FOOTPRINT}
        self.user = MagicMock()
        self.user.id = 1234
        self.galaxy_list = MagicMock()
        self.galaxy_list.id = 1
        self.galaxy_list.submitterid = 1234
        self.mock_gw_alert = MagicMock()
        self.mock_gw_alert.graceid = 'graceid'
        self.valid_timesent_stamp = '2019-05-01T12:00:00.00'
        self.valid_galaxies = [{'ra': 0.0, 'dec': 0.0, 'score': 0.0, 'groupname': 'test_group'}]
        self.galaxy = MagicMock()
        self.galaxy_entry = [self.galaxy]

    @patch('src.api_v1.db')
    def test_initial_request_parse_valid_json(self, mock_db):
        mock_request = MagicMock()
        mock_request.get_json.return_value = {'api_token': 'valid_token'}
        mock_db.session.query().filter().first.return_value = MagicMock()
        valid, message, args, user = initial_request_parse(mock_request, only_json=True)
        self.assertTrue(valid)
        self.assertEqual(message, '')
        self.assertIsNotNone(args)
        self.assertIsNotNone(user)

    @patch('src.api_v1.db')
    def test_initial_request_parse_invalid_json(self, mock_db):
        mock_request = MagicMock()
        mock_request.get_json.side_effect = Exception()
        valid, message, args, user = initial_request_parse(mock_request, only_json=True)
        self.assertFalse(valid)
        self.assertEqual(message, 'Endpoint only accepts json argument parameters')
        self.assertIsNone(args)
        self.assertIsNone(user)

    @patch('src.api_v1.db')
    def test_initial_request_parse_missing_token(self, mock_db):
        mock_request = MagicMock()
        mock_request.get_json.return_value = {}
        valid, message, args, user = initial_request_parse(mock_request, only_json=True)
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

    @patch('src.api_v1.db')
    def test_valid_request_returns_footprints(self, mock_db):
        response = self.client.get('/api/v1/footprints?api_token=token', headers={'Authorization': f'Bearer {self.valid_token}'})
        assert response.status_code == 200
        assert response.json is not None

    @patch('src.api_v1.db')
    def test_invalid_request_returns_error(self, mock_db):
        response = self.client.get('/api/v1/footprints')
        assert response.status_code == 500

    @patch('src.api_v1.db')
    def test_valid_id_returns_correct_footprint(self, mock_db):
        mock_db.session.query().filter().all.return_value = [self.footprint]
        response = self.client.get(f'/api/v1/footprints?id={self.footprint.instrumentid}&api_token=token', headers={'Authorization': f'Bearer {self.valid_token}'})
        assert response.status_code == 200
        assert len(response.json) == 1
        assert response.json[0]['instrumentid'] == INSTRUMENT_ID

    @patch('src.api_v1.db')
    def test_valid_name_returns_correct_footprint(self, mock_db):
        mock_db.session.query().filter().all.return_value = [self.footprint]
        response = self.client.get(f'/api/v1/footprints?name={INSTRUMENT_NAME}&api_token=token', headers={'Authorization': f'Bearer {self.valid_token}'})
        assert response.status_code == 200
        assert len(response.json) > 0
        assert any(fp['instrumentid'] == INSTRUMENT_ID for fp in response.json)

    @patch('src.api_v1.db')
    def test_invalid_id_returns_empty_list(self, mock_db):
        response = self.client.get('/api/v1/footprints?id=9999&api_token=token', headers={'Authorization': f'Bearer {self.valid_token}'})
        assert response.status_code == 200
        assert len(response.json) == 0

    @patch('src.api_v1.db')
    def test_invalid_name_returns_empty_list(self, mock_db):
        response = self.client.get('/api/v1/footprints?name=nonexistent&api_token=token', headers={'Authorization': f'Bearer {self.valid_token}'})
        assert response.status_code == 200
        assert len(response.json) == 0

    @patch('src.api_v1.db')
    def test_valid_listid_deletes_galaxy_list(self, mock_db):
        mock_db.session.query().filter().first.side_effect = [self.user, self.galaxy_list]
        response = self.client.post('/api/v1/remove_event_galaxies', json={'listid': self.galaxy_list.id, 'api_token':self.valid_token}, headers={'Authorization': f'Bearer {self.valid_token}'})
        assert response.status_code == 200
        assert response.data.decode() == 'Successfully deleted your galaxy list'

    @patch('src.api_v1.db')
    def test_invalid_listid_returns_error(self, mock_db):
        response = self.client.post('/api/v1/remove_event_galaxies', json={'listid': 'invalid', 'api_token':self.valid_token}, headers={'Authorization': f'Bearer {self.valid_token}'})
        assert response.status_code == 500
        assert response.data.decode() == 'Invalid listid'

    @patch('src.api_v1.db')
    def test_missing_listid_returns_error(self, mock_db):
        response = self.client.post('/api/v1/remove_event_galaxies', json={'api_token':self.valid_token}, headers={'Authorization': f'Bearer {self.valid_token}'})
        assert response.status_code == 500
        assert response.data.decode() == 'Event galaxy listid is required'

    @patch('src.api_v1.db')
    def test_unauthorized_user_returns_error(self, mock_db):
        self.galaxy_list.submitterid = 9999
        mock_db.session.query().filter().first.side_effect = [self.user, self.galaxy_list]
        response = self.client.post('/api/v1/remove_event_galaxies', json={'listid': self.galaxy_list.id, 'api_token':self.valid_token}, headers={'Authorization': f'Bearer {self.valid_token}'})
        assert response.status_code == 500
        assert response.data.decode() == 'You can only delete information related to your api_token! shame shame'

    @patch('src.api_v1.db')
    def test_non_existent_listid_returns_error(self, mock_db):

        mock_db.session.query().filter().first.side_effect = [self.user, None]

        response = self.client.post('/api/v1/remove_event_galaxies', json={'listid': 9999, 'api_token':self.valid_token}, headers={'Authorization': f'Bearer {self.valid_token}'})
        assert response.status_code == 500
        assert response.data.decode() == 'No galaxies with that listid'

    @patch('src.api_v1.db')
    def test_valid_graceid_returns_galaxy_entries(self, mock_db):
        models.db = mock_db
        mock_db.session.query().filter().all.side_effect = [self.mock_gw_alert, self.galaxy_entry]

        response = self.client.get('/api/v1/event_galaxies?graceid=valid_graceid&api_token=token',headers={'Authorization': f'Bearer {self.valid_token}'})
        assert response.status_code == 200
        assert response.is_json == True

    @patch('src.api_v1.db')
    def test_invalid_timesent_stamp_returns_error(self, mock_db):
        models.db  = mock_db
        response = self.client.get('/api/v1/event_galaxies?graceid=valid_graceid&timesent_stamp=invalid&api_token=token', headers={'Authorization': f'Bearer {self.valid_token}'})
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data.decode(), "Error parsing date. Should be %Y-%m-%dT%H:%M:%S.%f format. e.g. 2019-05-01T12:00:00.00")

    @patch('src.api_v1.db')
    def test_valid_timesent_stamp_returns_galaxy_entries(self, mock_db):
        models.db = mock_db
        mock_db.session.query().filter().all.side_effect = [self.mock_gw_alert, self.galaxy_entry]
        response = self.client.get('/api/v1/event_galaxies?graceid=valid_graceid&timesent_stamp=2019-05-01T12:00:00.00&api_token=token', headers={'Authorization': f'Bearer {self.valid_token}'})

        assert response.status_code == 200
        assert response.is_json == True

    @patch('src.api_v1.db')
    def test_invalid_listid_returns_error(self, mock_db):
        models.db = mock_db
        response = self.client.get('/api/v1/event_galaxies?graceid=valid_graceid&listid=invalid&api_token=token', headers={'Authorization': f'Bearer {self.valid_token}'})
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data.decode(), 'Invalid \'listid\'')

    @patch('src.api_v1.db')
    def test_valid_listid_returns_galaxy_entries(self, mock_db):
        models.db = mock_db
        mock_db.session.query().filter().all.side_effect = [self.mock_gw_alert, self.galaxy_entry]
        response = self.client.get('/api/v1/event_galaxies?graceid=valid_graceid&listid=1&api_token=token', headers={'Authorization': f'Bearer {self.valid_token}'})

        assert response.status_code == 200
        assert response.is_json == True

    @patch('src.api_v1.db')
    def test_valid_groupname_returns_galaxy_entries(self, mock_db):
        models.db = mock_db
        mock_db.session.query().filter().all.side_effect = [self.mock_gw_alert, self.galaxy_entry]
        response = self.client.get('/api/v1/event_galaxies?graceid=valid_graceid&groupname=test_group&api_token=token', headers={'Authorization': f'Bearer {self.valid_token}'})

        assert response.status_code == 200
        assert response.is_json == True


    @patch('src.api_v1.db')
    def test_valid_score_gt_returns_galaxy_entries(self, mock_db):
        models.db = mock_db
        mock_db.session.query().filter().all.side_effect = [self.mock_gw_alert, self.galaxy_entry]
        response = self.client.get('/api/v1/event_galaxies?graceid=valid_graceid&score_gt=0.5&api_token=token', headers={'Authorization': f'Bearer {self.valid_token}'})

        assert response.status_code == 200
        assert response.is_json == True


    @patch('src.api_v1.db')
    def test_valid_score_lt_returns_galaxy_entries(self, mock_db):
        models.db = mock_db
        mock_db.session.query().filter().all.side_effect = [self.mock_gw_alert, self.galaxy_entry]
        response = self.client.get('/api/v1/event_galaxies?graceid=valid_graceid&score_lt=1.5&api_token=token', headers={'Authorization': f'Bearer {self.valid_token}'})

        assert response.status_code == 200
        assert response.is_json == True

    @patch('src.api_v1.db')
    def test_post_event_galaxies_v1_valid_request(self, mock_db):
        models.db = mock_db
        response = self.client.post('/api/v1/event_galaxies', json={
            'api_token': 'token',
            'graceid': 'valid_graceid',
            'timesent_stamp': self.valid_timesent_stamp,
            'galaxies': self.valid_galaxies
        })
        assert response.status_code == 200
        assert 'Successful adding of' in response.data.decode()

    @patch('src.api_v1.db')
    def test_post_event_galaxies_v1_invalid_api_token(self, mock_db):
        models.db = mock_db
        response = self.client.post('/api/v1/event_galaxies', json={
            'api_token': 'invalid',
            'graceid': 'valid_graceid',
            'timesent_stamp': self.valid_timesent_stamp,
            'galaxies': self.valid_galaxies
        })
        assert response.status_code == 500
        assert response.data.decode() == 'invalid api_token'

    @patch('src.api_v1.db')
    def test_post_event_galaxies_v1_missing_api_token(self, mock_db):
        response = self.client.post('/api/v1/event_galaxies', json={
            'graceid': 'valid_graceid',
            'timesent_stamp': self.valid_timesent_stamp,
            'galaxies': self.valid_galaxies
        })
        assert response.status_code == 500
        assert response.data.decode() == 'api_token is required'

    @patch('src.api_v1.db')
    def test_post_event_galaxies_v1_invalid_graceid(self, mock_db):
        response = self.client.post('/api/v1/event_galaxies', json={
            'api_token': 'valid_api_token',
            'graceid': 'invalid_graceid',
            'timesent_stamp': self.valid_timesent_stamp,
            'galaxies': self.valid_galaxies
        })
        assert response.status_code == 500
        assert response.data.decode() == 'Invalid graceid'

    @patch('src.api_v1.db')
    def test_post_event_galaxies_v1_missing_graceid(self, mock_db):
        response = self.client.post('/api/v1/event_galaxies', json={
            'api_token': 'valid_api_token',
            'timesent_stamp': self.valid_timesent_stamp,
            'galaxies': self.valid_galaxies
        })
        assert response.status_code == 500
        assert response.json['message'] == 'graceid is required'

    @patch('src.api_v1.db')
    def test_post_event_galaxies_v1_invalid_timesent_stamp(self, mock_db):
        response = self.client.post('/api/v1/event_galaxies', json={
            'api_token': 'valid_api_token',
            'graceid': 'valid_graceid',
            'timesent_stamp': self.invalid_timesent_stamp,
            'galaxies': self.valid_galaxies
        })
        assert response.status_code == 500
        assert 'Error parsing date' in response.json['message']

    @patch('src.api_v1.db')
    def test_post_event_galaxies_v1_missing_timesent_stamp(self, mock_db):
        response = self.client.post('/api/v1/event_galaxies', json={
            'api_token': 'valid_api_token',
            'graceid': 'valid_graceid',
            'galaxies': self.valid_galaxies
        })
        assert response.status_code == 500
        assert response.json['message'] == 'timesent_stamp is required'

    @patch('src.api_v1.db')
    def test_post_event_galaxies_v1_missing_galaxies(self, mock_db):
        response = self.client.post('/api/v1/event_galaxies', json={
            'api_token': 'valid_api_token',
            'graceid': 'valid_graceid',
            'timesent_stamp': self.valid_timesent_stamp
        })
        assert response.status_code == 500
        assert response.json['message'] == 'a list of galaxies is required'

if __name__ == '__main__':
    unittest.main()