# Unit testing
import unittest
# Use requests library for HTTP requests
import requests
# Parse/split a url link
import urllib.parse
# Working with JSON data
import os, sys, json
# Utilize a familiar format: dataframes
import pandas as pd
# Binning for histograms
import numpy as np
# Plotting
import matplotlib.pyplot as plt
# Handling date and time information
import datetime

class TestAPI(unittest.TestCase):
  BASE = 'http://127.0.0.1:5000/api/v1' # Base address
  API_TOKEN = os.environ.get('api_token', '') # API token
  TARGET_POINTINGS = "pointings"
  TARGET_FOOTPRINTS = "footprints"
  TARGET_EVENT_GALAXIES = "event_galaxies"
  TARGET_GLADE = "glade"
  TARGET_INSTRUMENTS = "instruments"
  TARGET_MOC = "grb_moc_file"
  TARGET_QUERY = "query_alerts"
  INSTRUMENT_NAME = "Sinistro"
  INSTRUMENT_ID = 9
  GRACE_ID = "GW190814"
  MS_GRACE_ID = "MS230615e"
  TARGET_GALAXY = "event_galaxies"
  TARGET_GALAXY_REMOVE = "remove_event_galaxies"
  TARGET_DOI = "request_doi"
  TARGET_UPDATE_POINTINGS = "update_pointings"
  TARGET_CANCEL_ALL = "cancel_all"
  TARGET_FIX_DATA = "fixdata"

  ### GET Method tests

  # @JSON parameters: graceid, graceids, band, bands, status, completed_after, completed_before, user, users,
  # instrument, instruments, wavelength, frequency and energy regimes
  def test_get_pointings(self):
    """A get request for pointings"""
    json_params = {
        "api_token": self.API_TOKEN,
        "band":"XRT",
        "status":"completed",
        "graceid": self.GRACE_ID
    }

    url = "{}/{}".format(self.BASE, self.TARGET_POINTINGS)
    r = requests.get(url=url, json=json_params)
    print("Test 1 [Pointings for " + self.GRACE_ID + " event] passed")
    print(r.text)

  # @JSON parameters: id, name
  def test_footprints(self):
    """A get request for a footprints"""
    json_params = {
        "api_token": self.API_TOKEN,
        "id" : self.INSTRUMENT_ID,
        "name" : self.INSTRUMENT_NAME
    }

    url = "{}/{}".format(self.BASE, self.TARGET_FOOTPRINTS)
    r = requests.get(url=url, json=json_params)
    print("Test 1 [Footprints for " + self.GRACE_ID + " event] passed")
    print(r.text)

  # @JSON parameters: graceid, timesent_stamp, listid, groupname, score_gt, score_lt
  def test_get_event_galaxy(self):
    """A get request for a event galaxy"""
    json_params = {
        "api_token": self.API_TOKEN,
        "id" : self.INSTRUMENT_ID,
        "name" : self.INSTRUMENT_NAME,
        "graceid": "graceid1",
        "groupname": "groupname1",
        "score_lt": 0.01
    }

    url = "{}/{}".format(self.BASE, self.TARGET_EVENT_GALAXIES)
    r = requests.get(url=url, json=json_params)
    print("Test 1 [Event Galaxies for " + self.GRACE_ID + " event] passed")
    print(r.text)

  # @JSON parameters: RA, DEC, name
  def test_glade(self):
    """Test a request for a glade"""
    json_params = {
        "api_token": self.API_TOKEN,
        "id" : self.INSTRUMENT_ID,
        #ra
        #dec
        "name" : self.INSTRUMENT_NAME
    }

    url = "{}/{}".format(self.BASE, self.TARGET_GLADE)
    r = requests.get(url=url, json=json_params)
    print("Test 1 glade passed")
    print(r.text)

  # @JSON parameters: id, ids, name, names
  def test_instrument(self):
    """Test a get request for an instrument"""
    json_params = {
        "api_token": self.API_TOKEN,
        "id" : self.INSTRUMENT_ID,
        "name" : self.INSTRUMENT_NAME,
        "type":"photometric"
    }

    url = "{}/{}".format(self.BASE, self.TARGET_INSTRUMENTS)
    r = requests.get(url=url, json=json_params)
    print("Test 1 test_instrument passed")
    print(r.text)

  # @JSON parameters: id, name, graceid, instrument
  def test_moc(self):
    """Test a get request for a multi-order coverage"""
    json_params = {
        "api_token": self.API_TOKEN,
        "id" : self.INSTRUMENT_ID,
        "name" : self.INSTRUMENT_NAME,
        "graceid": self.GRACE_ID,
        "instrument": "gbm"
    }

    url = "{}/{}".format(self.BASE, self.TARGET_MOC)
    r = requests.get(url=url, json=json_params)
    print("Test 1 grab moc file passed")
    print(r.text)

  # @JSON parameters: id, name, graceid
  def test_query(self):
    """Test a query"""
    json_params = {
        "api_token": self.API_TOKEN,
        "id" : self.INSTRUMENT_ID,
        "name" : self.INSTRUMENT_NAME,
        "graceid": self.GRACE_ID
    }

    url = "{}/{}".format(self.BASE, self.TARGET_QUERY)
    r = requests.get(url=url, json=json_params)
    if (r.status_code == 200):
      print("Test 1 query passed")
      print(r.text)
    else:
      print("Test 1 query failed")
      print(r.text)

  ### POST Method tests
  # @JSON parameters: id, timesent_stamp
  def test_post_event_galaxy(self):
    json_params = {
        "api_token": self.API_TOKEN,
        "id" : self.INSTRUMENT_ID,
        "timesent_stamp":"2019-05-22T12:33:59"
    }

    url = "{}/{}".format(self.BASE, self.TARGET_GALAXY)
    r = requests.post(url=url, json=json_params)
    print("Test 1 post event galaxy passed")
    print(r.text)

  # @JSON parameters: id, timesent_stamp
  def test_remove_event_galaxy(self):
    json_params = {
        "api_token": self.API_TOKEN,
        "id" : self.INSTRUMENT_ID,
        "timesent_stamp":"2019-05-22T12:33:59"
    }

    url = "{}/{}".format(self.BASE, self.TARGET_GALAXY_REMOVE)
    r = requests.post(url=url, json=json_params)
    print("Test 2 remove event galaxy passed")
    print(r.text)

  '''
   1.) post a pointing to one of the test events (gw events that start with 'MS...') status is planned, save the pointing ID
    ->do an update on the pointing (update status=completed)
   2.) post another pointing to one of the test events (gw events that start with 'MS...') status is planned, save the pointing ID
    ->do an update on the pointing (update status=cancelled)
   3.) post another pointing to one of the test events (gw events that start with 'MS...') status = completed, save the pointing ID
  '''
  # @JSON parameters: graceid, pointings
  def test_post_pointings(self):
    """Posts new pointings"""
    json_params = {
      "api_token": self.API_TOKEN,
      "graceid": self.MS_GRACE_ID,
      "pointings": [
        {
          "ra":42,
          "dec":42.0,
          "band":"V",
          "instrumentid":"20",
          "depth":"19.5",
          "depth_unit":"ab_mag",
          "time":"2019-05-22T12:30:59",
          "pos_angle":"45.0",
          "status":"completed"
        },
        {
          "position":"POINT(42 42)",
          "central_wave":6500,
          "bandwidth":1200,
          "wavelength_unit":"angstrom",
          "instrumentid":"instrumentname1",
          "depth":"5e-12",
          "depth_unit":"flux_erg",
          "time":"2019-05-22T12:30:59",
          "status":"planned"
        },
        {
          "position":"POINT(42 42)",
          "energy_regime":[0.39,1.1],
          "energy_unit":"keV",
          "instrumentid":"Swift/XRT",
          "depth":"19.5",
          "depth_unit":"ab_mag",
          "time":"2019-05-22T12:30:59",
          "status":"planned"
        }
      ]
    }

    url = "{}/{}".format(self.BASE, self.TARGET_POINTINGS)
    r = requests.post(url=url, json=json_params)
    print("Test 2 post for pointings passed")
    print(r.text)

  # @JSON parameters: graceid, creators
  def test_request_doi(self):
    """Request a batch DOI for completed pointings"""
    json_params = {
      "api_token": self.API_TOKEN,
      "graceid": self.GRACE_ID,
      "creators":[
        {"name":"Name1", "affiliation":"affil_1"},
        {"name":"Name2", "affiliation":"affil_2"}
      ]
    }
    url = "{}/{}".format(self.BASE, self.TARGET_DOI)
    r = requests.post(url=url, json=json_params)
    print("Test 1 post for request doi passed")
    print(r.text)

  # @JSON parameters: graceid, ids, status
  def test_update_pointings(self):
    """Cancels planned pointings"""
    json_params = {
      "api_token": self.API_TOKEN,
      "graceid": self.GRACE_ID,
      "ids":[42,43,44,45],
      "status":"cancelled"
    }
    url = "{}/{}".format(self.BASE, self.TARGET_UPDATE_POINTINGS)
    r = requests.post(url=url, json=json_params)
    print("Test 1 post for updating pointings passed")
    print(r.text)

  # @JSON parameters: graceid, instrumentid, status
  def test_cancel_pointings(self):
    """Cancels planned pointings"""
    json_params = {
      "api_token": self.API_TOKEN,
      "graceid":"TEST_EVENT",
      "instrumentid": 1,
      "status":"cancelled"
    }
    url = "{}/{}".format(self.BASE, self.TARGET_CANCEL_ALL)
    r = requests.post(url=url, json=json_params)
    print("Test 1 post for cancelling all pointings passed")
    print(r.text)

   # @JSON parameters: graceid, instrumentid, status
  def test_fix_data(self):
    """Fills in missing information for central frequency and duration"""
    json_params = {
      "api_token": self.API_TOKEN
    }
    url = "{}/{}".format(self.BASE, self.TARGET_FIX_DATA)
    r = requests.post(url=url, json=json_params)
    print("Test 1 post for fixing data")
    print(r.text)

if __name__ == "__main__":

  tester = TestAPI()

  # GET Requests
  tester.test_get_pointings()
  tester.test_footprints()
  tester.test_get_event_galaxy()
  tester.test_glade()
  tester.test_instrument()
  tester.test_moc()
  tester.test_query()

  # POST Requests
  tester.test_post_event_galaxy()
  tester.test_remove_event_galaxy()
  tester.test_post_pointings()
  tester.test_request_doi()
  tester.test_update_pointings()
  tester.test_cancel_pointings()
  tester.test_fix_data()
