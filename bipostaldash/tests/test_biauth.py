#import webtest
import os
import unittest2

from pyramid import testing
#from pyramid import httpexceptions as httpx
from nose.tools import eq_

from bipostaldash.storage import mem
from bipostaldash.auth.browserid import BrowserIDAuth

class BrowerIDTest(unittest2.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        path = os.path.join('bipostaldash', 'tests', 'assert.txt')
        self.assertion = open(path).read().strip()
        self.auth = BrowserIDAuth(auth_server='browserid.org')

    def tearDown(self):
        testing.tearDown()

    def test_authenticate(self):
        request = testing.DummyRequest()
        request.params['assertion'] = self.assertion
        request.registry['storage'] = mem.Storage()
        response = self.auth.get_user_id(request)
        eq_(response, 'test@unitedheroes.net')

