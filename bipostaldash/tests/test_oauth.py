import unittest2
import os

from pyramid import testing
from nose.tools import (eq_, assert_raises)
from bipostaldash.auth.oauth import (OAuth, OAuthException)

class OAuthTest(unittest2.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        self.auth = OAuth()

    def tearDown(self):
        testing.tearDown()

    def test_authenticate(self):
        request = testing.DummyRequest()
        request.params['email'] = 'foo@example.com'
        request.path = '/test'
        request.method = 'GET'
        request.params = {'a': 1, 'email': 'test@example.com'}

        request.registry['oauth_params'] = {
                'oauth_consumer_key': '123',
                'oauth_nonce': '1234',
                'oauth_timestamp': 1323283311,
                'oauth_signature': 'gjKO7mKe7pRZ%2BsPlVnSgkAend3g%3D',
                'oauth_signature_method': 'HMAC-SHA1',
                'oauth_version': '1.0'}
        request.registry['config'] = {
                'auth.oauth.consumer_key': '123',
                'auth.oauth.shared_secret': 'abc'}
        request.session = \
            {'uid': request.params['email']}
        authElem = []
        for key in request.registry['oauth_params']:
            authElem.append('%s="%s"' % (key, 
                request.registry['oauth_params'][key]))
        authLine = 'OAuth %s' % ', '.join(authElem)
        request.headers['Authorization'] = authLine
        r_email = self.auth.get_user_id(request)
        eq_(r_email, request.params['email'])
        # Replay check
        assert_raises(OAuthException, 
                self.auth.get_user_id,
                request)
        



         
