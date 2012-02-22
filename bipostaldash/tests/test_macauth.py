import unittest2
import time
import base64
import hashlib
import hmac
import urllib

from bipostaldash.auth.mac_auth import (MacAuth, MacAuthException)
from nose.tools import (eq_, assert_raises)
from pyramid import testing


class MacAuthTest(unittest2.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        self.auth = MacAuth()

    def tearDown(self):
        testing.tearDown()

    def test_authenticate(self):
        request = testing.DummyRequest()
        email  = 'test@example.com'
        request.server_port = 80 
        request.path_info = '/testing'
        authItems = {'access_token': 'access',
                    'mac_key': 'key',
                    'host': request.host.split(':')[0],
                    'port': str(request.server_port),
                    'uri': request.path_info,
                    'action': 'GET',
                    'timestamp': str(int(time.time())),
                    'nonce': 'nonce',
                    'ext': ''
                    }
        authItems['sbs'] = ("%s\n%s\n%s\n%s\n%s\n%s\n%s\n" % (
            authItems['timestamp'],
            authItems['nonce'],
            authItems['action'],
            authItems['uri'],
            authItems['host'],
            authItems['port'],
            authItems['ext']))

        authItems['mac'] = base64.b64encode(hmac.new(authItems['mac_key'],
            authItems['sbs'],
            hashlib.sha1).digest())

        request.registry['config'] = {
                'auth.oauth.consumer_key': '123',
                'auth.oauth.shared_secret': 'abc'}
        request.session = \
            {'uid': email,
             'auth.mac_type': 'mac-sha-1',
             'keys': {'access_token': authItems['access_token'],
                     'mac_key': authItems['mac_key']}}
        
        authLine = 'MAC id="%s" ts="%s" nonce="%s" ext="%s" mac="%s"' % (
                authItems['access_token'],
                authItems['timestamp'],
                authItems['nonce'],
                urllib.urlencode(authItems['ext']),
                authItems['mac'])
        request.headers['Authorization'] = authLine
        # test signer
        result = self.auth.sign(authItems['access_token'],
                authItems['mac_key'],
                request,
                nonce=authItems['nonce'])
        eq_(result['items']['mac'], authItems['mac'])
        # test validator
        r_email = self.auth.get_user_id(request)
        eq_(r_email, email)
        # Replay check
        assert_raises(MacAuthException,
                self.auth.get_user_id,
                request)
