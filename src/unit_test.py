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
  TARGET_1 = "pointings"
  TARGET_2 = "footprints"
  TARGET_3 = "event_galaxies"
  INSTRUMENT_NAME = "Sinistro"
  INSTRUMENT_ID = 9
  GRACE_ID = "GW190814"

  ### GET Method tests
  def test_pointings_1(self):
    json_params = {
        "api_token": self.API_TOKEN,
        "band":"XRT",
        "status":"completed",
        "graceid": self.GRACE_ID
      }
    url = "{}/{}".format(self.BASE, self.TARGET_1)
    r = requests.get(url=url, json=json_params)
    self.assertEqual(r.status_code, 200)
    #self.assertEqual(len(r.json()), 483)
    print("Test 1 [Pointings for " + self.GRACE_ID + " event] passed")
    print(r.text)

  def test_footprints_1(self):
    json_params = {
        "api_token": self.API_TOKEN,
        "id" : self.INSTRUMENT_ID,
        "name" : self.INSTRUMENT_NAME
      }
    url = "{}/{}".format(self.BASE, self.TARGET_2)
    r = requests.get(url=url, json=json_params)
    self.assertEqual(r.status_code, 200)
    print("Test 1 [Footprints for " + self.GRACE_ID + " event] passed")
    print(r.text)

  def test_event_galaxy_1(self):
    json_params = {
        "api_token": self.API_TOKEN,
        "id" : self.INSTRUMENT_ID,
        "name" : self.INSTRUMENT_NAME
      }
    url = "{}/{}".format(self.BASE, self.TARGET_3)
    r = requests.get(url=url, json=json_params)
    #self.assertEqual(r.status_code, 200)
    print("Test 1 [Event Galaxies for " + self.GRACE_ID + " event] passed")
    print(r.text)

  ### POST Method tests


if __name__ == "__main__":
  tester = TestAPI()
  tester.test_pointings_1()
  tester.test_footprints_1()
  tester.test_even_galaxy_1()