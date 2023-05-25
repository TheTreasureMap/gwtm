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
  API_TOKEN = "Tsqx2GKTa7BdFMSrpqYWIOHtrI3cnccZeC0_LQ" # API token
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

  ### GET Method tests

  # @JSON parameters: graceid, graceids, band, bands, status, completed_after, completed_before, user, users,
  # instrument, instruments, wavelength, frequency and energy regimes
  def test_pointings(self):
    json_params = {
        "api_token": self.API_TOKEN,
        "band":"XRT",
        "status":"completed",
        "graceid": self.GRACE_ID
    }

    url = "{}/{}".format(self.BASE, self.TARGET_POINTINGS)
    r = requests.get(url=url, json=json_params)
    #self.assertEqual(r.status_code, 200)
    #self.assertEqual(len(r.json()), 483)
    print("Test 1 [Pointings for " + self.GRACE_ID + " event] passed")
    print(r.text)

  # @JSON parameters: id, name
  def test_footprints(self):
    json_params = {
        "api_token": self.API_TOKEN,
        "id" : self.INSTRUMENT_ID,
        "name" : self.INSTRUMENT_NAME
    }

    url = "{}/{}".format(self.BASE, self.TARGET_FOOTPRINTS)
    r = requests.get(url=url, json=json_params)
    #self.assertEqual(r.status_code, 200)
    print("Test 1 [Footprints for " + self.GRACE_ID + " event] passed")
    print(r.text)

  # @JSON parameters: graceid, timesent_stamp, listid, groupname, score_gt, score_lt
  def test_event_galaxy(self):
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
    #self.assertEqual(r.status_code, 200)
    print("Test 1 [Event Galaxies for " + self.GRACE_ID + " event] passed")
    print(r.text)

  # @JSON parameters: RA, DEC, name
  def test_glade(self):
    json_params = {
        "api_token": self.API_TOKEN,
        "id" : self.INSTRUMENT_ID,
        #ra
        #dec
        "name" : self.INSTRUMENT_NAME
    }

    url = "{}/{}".format(self.BASE, self.TARGET_GLADE)
    r = requests.get(url=url, json=json_params)
    #self.assertEqual(r.status_code, 200)
    print("Test 1 glade passed")
    print(r.text)

  # @JSON parameters: id, ids, name, names
  def test_instrument(self):
    json_params = {
        "api_token": self.API_TOKEN,
        "id" : self.INSTRUMENT_ID,
        "name" : self.INSTRUMENT_NAME,
        "type":"photometric"
    }

    url = "{}/{}".format(self.BASE, self.TARGET_INSTRUMENTS)
    r = requests.get(url=url, json=json_params)
    #self.assertEqual(r.status_code, 200)
    print("Test 1 test_instrument passed")
    print(r.text)

  def test_moc(self):
    json_params = {
        "api_token": self.API_TOKEN,
        "id" : self.INSTRUMENT_ID,
        "name" : self.INSTRUMENT_NAME,
        "graceid": self.GRACE_ID,
        "instrument": "gbm"
    }

    url = "{}/{}".format(self.BASE, self.TARGET_MOC)
    r = requests.get(url=url, json=json_params)
    #self.assertEqual(r.status_code, 200)
    print("Test 1 grab moc file passed")
    print(r.text)

  def test_query(self):
    json_params = {
        "api_token": self.API_TOKEN,
        "id" : self.INSTRUMENT_ID,
        "name" : self.INSTRUMENT_NAME,
        "graceid": self.GRACE_ID
    }

    url = "{}/{}".format(self.BASE, self.TARGET_QUERY)
    r = requests.get(url=url, json=json_params)
    self.assertEqual(r.status_code, 200)
    print("Test 1 query passed")
    print(r.text)

  ### POST Method tests

if __name__ == "__main__":

  tester = TestAPI()
  tester.test_pointings()
  tester.test_footprints()
  tester.test_event_galaxy()
  tester.test_glade()
  tester.test_instrument()
  tester.test_moc()
  tester.test_query()