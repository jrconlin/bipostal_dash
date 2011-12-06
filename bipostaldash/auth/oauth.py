import urllib2
import re

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

def _oEsc(string):
    if not string:
        return ''
    string = urllib2.quote(string)
    return string.replace('/', '%2F').replace('+', '%20')\
            .replace('!', '%21').replace('*', '%2A')\
            .replace('\\', '%27').replace('(', '%28').\
            replace(')', '%29')


def normalizedParams(params):
    if not params:
        return ''
    elements = []
    pkeys = params.keys()
    pkeys.sort()
    for pname in pkeys:
        if '_secret' in pname:
            continue
        pvalue = params.get(pname)
        if type(pvalue) == type([]):
            pvalue.sort()
            for value in pvalue:
                elements.append("%s=%s" % (_oEsc(pname),
                                           _oEsc(value)))
            next
        else:
            elements.append("%s=%s" % (_oEsc(pname),
                                       _oEsc(pvalue)))
    return '&'.join(elements)


def sign(method, path, tokens, params, keys):
    sbs = '&'.join((method.upper(),
                    path.upper(),
                    normalizedParams(params)))
    



def authenticated_userid(request):
    reg = request.registry
    params = request.params

    # Do we have keys?
    try:
        public_key = reg['config']['oauth.public_key']
        private_key = reg['config']['oauth.private_key']
    except KeyError, e:
        raise Exception('Config missing keys: "%s"' %
                                   str(e))
    # Is this an OAuth request?
    if 'Authorization' in request.headers:
        auth_header = request.headers.get("Authorization")
        if not auth_header.startswith('OAuth '):
            raise Exception('Request is not signed using OAuth')
        oauth_token = {}
        for match in re.finditer('(\w+)="(\w+)"'):
            group = match.groups()
            oauth_token[group[0]] = group[1]
    else:
        for param in params:
            if param.startswith('oauth_'):
                oauth_token[param] = params.get(param)
                del(params[param])
    # Do we have the required OAuth values?
    required_keys = ['oauth_nonce',
                     'oauth_timestamp',
                     'oauth_consumer_key',
                     'oauth_signature_method',
                     'oauth_signature',
                     'oauth_version']
    for key in required_keys:
        if key not in oauth_token:
            raise Exception('Request missing required OAuth values')
    # Have we seen this nonce for this public_key before?
    if (nonces.contains(oauth_token['oauth_nonce'])):
        raise Exception('Repeated oauth_nonce')
    path = request.path
    method = request.method
    # Build the comparison SBS
    signature = sign(method=method,
                        path=path,
                        tokens=oauth_token,
                        params=params)
    # and generate the sig

    # Compare the comparison sig with the recv'd signature.
