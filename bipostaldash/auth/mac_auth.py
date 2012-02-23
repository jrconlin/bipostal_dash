import base64
import hashlib
import hmac
import logging
import random
import re
import string
import time
import urllib


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
    pass

class MacAuth(object):
    """ Absolutely minimal OAuth function to validate args and return
        an email. """

    validMacMethods = { 'mac-sha-1': hashlib.sha1,
            'mac-sha-256': hashlib.sha256}
    _port = None
    default_expry = 1

    def __init__(self, **kw):
        if ('server.port' in kw):
            self._port = kw.get('server.port')
        pass

    def genNonce(self, len=8):
        chars = string.digits + string.letters
        return ''.join(random.sample(chars, len))

    def getNormalizedRequestString(self, **args):
        normalizedRequestArray = [
                args.get('ts'),
                args.get('nonce'),
                args.get('method').upper(),
                args.get('request_uri'),
                args.get('host').split(':')[0],
                str(args.get('port','80')),
                args.get('ext','')]
        # remember to include the final "\n".
        return "\n".join(normalizedRequestArray) + "\n"

    def verifySig(self, str1, str2):
        """ Attempts to foil timing attacks on MAC sniffing """
        if (len(str1) != len(str2)):
            return False
            """ time to electrify the moat of lava """
        return 0 == (sum(ord(a) ^ ord(b) 
                    for a, b in zip(str1, str2)))

    def validate(self, request):
        headers = request.headers
        session = request.session
        config = request.registry.get('config', {})
        if "Authorization" not in headers:
            err = 'No Auth header present. Failing'
            logging.error(err)
            raise MacAuthException(err)
        auth = headers.get("Authorization")
        if auth[:3].upper() != 'MAC':
            err = 'Auth Header is not MAC. Failing'
            logging.error(err)
            raise MacAuthException(err)
        mac_key = request.session.get('keys',
                {}).get('mac_key', None);
        if mac_key is None:
            err = "Missing MAC key. Possibly result of uninitialized call. Failing"
            logging.error(err)
            raise MacAuthException(err)
        # Parse the exchanged elements from the MAC Auth line
        items = {}
        for (key, value) in re.findall('(\w+)="([^"]+)"', auth):
            items[key] = value
        request_uri = request.path_info
        # Check that the nonce is unique
        if nonces.contains(items['nonce']):
           logging.error("Duplicate Nonce, Replay? Failing")
           return False
        nonces.add(items['nonce'])
        # Check the timestamp against the known expry
        expry = int(session.get('expry', 
                config.get('auth.expry', self.default_expry)))
        if (expry and (int(time.time()) > expry + int(items['ts']))):
            logging.error("Expired Timestamp. Failing")
            return False
        # Gauntlet cleared, check the sbs.
        if request.query_string:
            request_uri += '?' + request.query_string
        sbs = self.getNormalizedRequestString(
            ts=items.get('ts'),
            nonce=items.get('nonce'),
            method=request.method,
            request_uri=request_uri,
            host=request.host,
            port=str(self._port or request.server_port),
            ext=items.get('ext', ''))
        logging.debug('Validate Normalized: "%s"' % sbs)
        macMethod = self.validMacMethods[session.get('auth.mac_type',
                'mac-sha-1')]
        testSig = base64.b64encode(hmac.new(mac_key, sbs, macMethod).digest())
        logging.debug('testing "%s" =? "%s"' % (testSig, items.get('mac')))
        return self.verifySig(testSig, items.get('mac'))

    def sign(self, access_token, mac_key, request, **kw):
        ts = str(kw.get('ts', int(time.time())))
        nonce = kw.get('nonce', self.genNonce())
        ext = urllib.urlencode(kw.get('ext', ''))
        nrs = self.getNormalizedRequestString(
            ts=ts,
            nonce=nonce,
            method=kw.get('method', 'GET').upper(),
            request_uri=request.path_info or '/',
            host=request.host or 'localhost',
            port=kw.get('port', request.server_port or '80'),
            ext=ext)
        logging.debug('Validate Normalized: "%s"' % nrs)
        macMethod = self.validMacMethods[kw.get('mac_type', 'mac-sha-1')]
        sig = base64.b64encode(hmac.new(mac_key, nrs, macMethod).digest())
        logging.debug('Signed as "%s"' % sig)
        return {'items': {
                   'id': access_token,
                   'ts': ts,
                    'nonce': nonce,
                    'ext': ext,
                    'mac': sig },
                 'sbs': nrs,
                 'header': 
                    'MAC id="%s" ts="%s" nonce="%s" ext="%s" mac="%s"' % (
                        access_token, ts, nonce, ext, sig)}

    def get_user_id(self, request):
        if self.validate(request):
            return request.session.get('uid')
        else:
            err = 'Invalid MAC, refusing user ID request.'
            logging.error(err)
            raise MacAuthException(err)

    def header(self, error=None):
        response = 'WWW-Authenticate: MAC'
        if error:
            response += 'error="%s"' % error.replace('"', '\\"')
        return response

    def gen_keys(self, access, secret, refresh, config, **kw):
        return {
                'token_type': 'mac',
                'access_token': access,
                'mac_key': secret,
                'refresh_token': refresh,
                'mac_algorithm': config.get('auth.mac_type', 'mac-sha-1'),
                'expires_in': config.get('auth.expry', 0),
                'server_time': int(time.time()),
                }


if __name__ == '__main__':
    class DummyRequest(dict):
        def __init__(self, **kw):
            self.path_info = '/'
            self.host = kw.get('host','localhost')
            self.server_port = kw.get('port', '80')
            self.method = kw.get('method', 'GET')
            self.query_string = None
            self.headers = {}
            self.session = {}
       

    test = MacAuth()
    request = DummyRequest(host='example.org')
    request.session = {'keys': {'access_token': 'access',
            'mac_key': 'secret'}}
    res = test.sign(request.session.get('keys').get('access_token'), 
            request.session.get('keys').get('mac_key'), request)
    request.headers['Authorization'] = res.get('header')
    if (not test.validate(request)):
        print "crap"
    print repr(res)
