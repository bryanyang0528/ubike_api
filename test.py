#!/usr/bin/env python

"""Tests for the Flask Heroku template."""

import unittest
import json
from app import app


class TestApp(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()

    def test_home_page_works(self):
        rv = self.app.get('/')
        self.assertTrue(rv.data)
        self.assertEqual(rv.status_code, 404)


    def test_404_page(self):
        rv = self.app.get('/i-am-not-found/')
        self.assertEqual(rv.status_code, 404)

    def test_update_sbi(self):
        rv = self.app.get('/update/sbi/')
        res = json.loads(rv.data)
        self.assertEqual(res['status'], 'successed')
        self.assertEqual(rv.status_code, 200)

    def test_update_station(self):
        rv = self.app.get('/update/stations/')
        res = json.loads(rv.data)
        self.assertEqual(res['status'], 'successed')
        self.assertEqual(rv.status_code, 200)

    def test_api_no_lon(self):
        rv = self.app.get('v1/ubike-station/taipei?lat=25.194153')
        res = json.loads(rv.data)
        self.assertEqual(res['code'], -1)
        self.assertEqual(res['result'], [])
        self.assertEqual(rv.status_code, 200)

    def test_api_no_lon(self):
        rv = self.app.get('v1/ubike-station/taipei?lat=25.194153')
        res = json.loads(rv.data)
        self.assertEqual(res['code'], -1)
        self.assertEqual(res['result'], [])
        self.assertEqual(rv.status_code, 200)

    def test_api_not_in_Taipei(self):
        rv = self.app.get('v1/ubike-station/taipei?lat=24.999087&lng=121.327547')
        res = json.loads(rv.data)
        self.assertEqual(res['code'], -2)
        self.assertEqual(res['result'], [])
        self.assertEqual(rv.status_code, 200)

    def test_api_in_Taipei(self):
        rv = self.app.get('v1/ubike-station/taipei?lat=25.034153&lng=121.568509')
        res = json.loads(rv.data)
        self.assertEqual(res['code'], 0)
        self.assertEqual(len(res['result']), 2)
        self.assertEqual(rv.status_code, 200)

    def test_api_in_north_Taipei(self):
        rv = self.app.get('v1/ubike-station/taipei?lat=25.194153&lng=121.568509')
        res = json.loads(rv.data)
        self.assertEqual(res['code'], 0)
        self.assertEqual(len(res['result']), 2)
        self.assertEqual(rv.status_code, 200)

    def test_api_wired_address_Taipei(self):
        rv = self.app.get('v1/ubike-station/taipei?lat=25.034153&lng=121.558509')
        res = json.loads(rv.data)
        self.assertEqual(res['code'], 0)
        self.assertEqual(len(res['result']), 2)
        self.assertEqual(rv.status_code, 200)

    def test_api_no_addr(self):
        rv = self.app.get('v1/ubike-station/taipei?lat=25.034153&lng=125.558509')
        res = json.loads(rv.data)
        self.assertEqual(res['code'], -2)
        self.assertEqual(len(res['result']), 0)
        self.assertEqual(rv.status_code, 200)

    def test_api_invalid_lat(self):
        rv = self.app.get('v1/ubike-station/taipei?lat=25.034153&lng=180.558509')
        res = json.loads(rv.data)
        self.assertEqual(res['code'], -1)
        self.assertEqual(len(res['result']), 0)
        self.assertEqual(rv.status_code, 200)


if __name__ == '__main__':
    unittest.main()
