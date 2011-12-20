import base64
import hashlib
import hmac
import urllib2
import re
from services import logging


class NonceRing(object):

    # Share a common
    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(NonceRing, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self, size=20):
        self.data = [None for i in range(0,size)]

    def add(self, val):
        self.data.pop(0)
        self.data.append(val)

    def contains(self, val):
        return val in self.data

nonces = NonceRing()


class OAuthException(Exception):
    def __init__(self, value):
        self.msg = value

    def __str__(self):
        return repr(self.msg)


class OAuth(object):
    """ Absolutely minimal OAuth function to validate args and return
        an email. """

    def __init__(self, **kw):
        pass

    def _oEsc(self, string):
        if not string:
            return ''
        string = urllib2.quote(str(string))
        return string.replace('/', '%2F').replace('+', '%20')\
                .replace('!', '%21').replace('*', '%2A')\
                .replace('\\', '%27').replace('(', '%28').\
                replace(')', '%29')


    def normalizedParams(self, params):
        if not params:
            return ''
        elements = []
        pkeys = params.keys()
        pkeys.sort()
        for pname in pkeys:
            if '_secret' in pname or pname == 'oauth_signature':
                continue
            pvalue = params.get(pname)
            if type(pvalue) == type([]):
                pvalue.sort()
                for value in pvalue:
                    elements.append("%s=%s" % (self._oEsc(pname),
                                               self._oEsc(value)))
                next
            else:
                elements.append("%s=%s" % (self._oEsc(pname),
                                           self._oEsc(pvalue)))
        return '&'.join(elements)


    def get_user_id(self, request):
        reg = request.registry
        params = request.params

        key_store = reg.get('key_store')

        # Is this an OAuth request?
        if 'Authorization' in request.headers:
            auth_header = request.headers.get("Authorization")
            if not auth_header.startswith('OAuth '):
                raise Exception('Request is not signed using OAuth')
            grp = re.compile('(\w+)="([^"]+)"')
            for match in grp.finditer(auth_header):
                group = match.groups()
                params[group[0]] = group[1]
        # Do we have keys?
        consumer_key = params.get('oauth_consumer_key')
        if not consumer_key:
            raise OAuthException('missing Consumer Key')
        shared_secret = key_store.get(consumer_key);
        if not shared_secret:
            raise OAuthException('invalid Shared Secret')
        # Do we have the required OAuth values?
        required_keys = ['oauth_nonce',
                         'oauth_timestamp',
                         'oauth_consumer_key',
                         'oauth_signature',
                         'oauth_signature_method',
                         'oauth_version']
        for key in required_keys:
            if key not in params:
                raise OAuthException('Request missing required OAuth value %s' % key)
        your_sig = urllib2.unquote(params.get('oauth_signature'))
        # Have we seen this nonce for this consumer_key before?
        if (nonces.contains(params['oauth_nonce'])):
            raise OAuthException('Repeated oauth_nonce')
        nonces.add(params['oauth_nonce'])
        path = request.path
        method = request.method
        # Build the comparison SBS
        sbs = '&'.join(((self._oEsc(method.upper())), 
                self._oEsc(path), 
                self._oEsc(self.normalizedParams(params))))
        # and generate the sig
        test_sig = base64.b64encode(hmac.new("%s&" % shared_secret,
            sbs, hashlib.sha1).digest())
        # Compare the comparison sig with the recv'd signature
        if (params.get('oauth_consumer_key') == consumer_key 
                and test_sig == your_sig):
            session = request.session
            return session.get('uid')
        logging.error("invalid signature")
        return None

