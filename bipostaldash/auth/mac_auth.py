import base64
import hashlib
import hmac
import logging
import random
import re
import string


class NonceRing(object):

    # Share a common
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(NonceRing, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self, size=20):
        self.data = [None for i in range(0, size)]

    def add(self, val):
        self.data.pop(0)
        self.data.append(val)

    def contains(self, val):
        return val in self.data

nonces = NonceRing()


class MacAuthException(Exception):

    def __init__(self,  msg):
        self.msg = msg

    def __str__(self):
        return repr(self.msg)


class MacAuth(object):
    """ Absolutely minimal OAuth function to validate args and return
        an email. """

    validMacMethods = { 'mac-sha-1': hashlib.sha1,
            'mac-sha-256': hashlib.sha256}

    def __init(self, **kw):
        pass

    def genNonce(self, len=8):
        chars = string.digits + string.letters
        return ''.join(random.sample(chars, len))

    def genNormalizedRequestString(self, **args):
        normalizedRequestArray = [
                args.get('ts'),
                args.get('nonce'),
                args.get('method').upper(),
                args.get('request_uri'),
                args.get('host'),
                args.get('port'),
                args.get('ext')]
        return '\n'.join(normalizedRequestArray)

    def validate(self, request):
        headers = request.headers
        session = request.session
        if "Authorization" not in headers:
            logging.error('No Auth header present. Failing')
            raise MacAuthException('No Authorization Header present')
        auth = headers.get("Authorization")
        if auth[:3].upper() != 'MAC':
            logging.error('Auth is not MAC. Failing')
            raise MacAuthException('Authorization is not MAC Auth type')
        mac_key = request.session.get('keys',
                {}).get('mac_key', None);
        if mac_key is None:
            logging.error('Missing MAC key. How did we get here?')
            raise MacAuthException('No MAC key defined')
        items = {}
        for (key, value) in map(re.findall('(\w+)="([^"]+)"', auth)):
            items[key] = value
        request_uri = request.path_info
        if request.query_string:
            request_uri += '?' + request.query_string
        nrs = self.getNormalizedRequestString(
            ts=items.get('ts'),
            nonce=items.get('nonce'),
            method=request.method,
            request_uri=request_uri,
            host=request.host,
            port=request.server_port,
            ext=items.get('ext'))
        logging.info('Normalized: "%s"' % nrs)
        macMethod = self.validMacMethods(session.get('auth.mac_type',
                'mac-sha-1'))
        testSig = base64.b64encode(hmac.new(mac_key, 
            nrs, macMethod).digest())
        logging.info('testing "%s" =? "%s"' % (testSig, items.get('mac')))
        return testSig == items.get('mac')

    def get_user_id(self, request):
        if self.validate(request):
            return request.session.get('uid')

    def header(self, error=None):
        response = 'WWW-Authenticate: MAC'
        if error:
            response += 'error="%s"' % error.replace('"', '\\"')
        return response

    def gen_keys(self, access, secret, refresh, config):
        return {
                'token_type': 'mac',
                'access_token': access,
                'mac_key': secret,
                'refresh_token': refresh,
                'mac_algorithm': config.get('auth.mac_type', 'mac-sha-1'),
                'expires_in': config.get('auth.expry', 0),
                }
