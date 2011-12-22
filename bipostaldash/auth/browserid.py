from StringIO import StringIO
from base64 import urlsafe_b64decode
from services import logger
import json
# urllib doesn't know https. pycurl does. 
import pycurl
import urllib
import urllib2


class BrowserIDAuth(object):

    def __init__(self, 
            **kw):
        pass

    def create_user(self, assertion=None, **kw):
        self._raw_assertion = assertion
        
    def get_user_id(self, 
            request, 
            audience=None,
            assertion=None):
        session = request.session
        if (session.get('uid')):
            return session.get('uid')
        if audience is None:
            audience = request.host
        if assertion is None and 'assertion' in request.params:
            assertion = \
             urllib2.unquote(request.params.get('assertion')).strip()
        if assertion is None:
            return None
        config = request.registry.get('config', {})
        try:
            if config.get('auth.local_auth', False):
                #note: this does not validate the assertion (yet).
                # Still need to pull the public key from the server
                parsed_cert = self._parse_assertion(assertion)
                return parsed_cert['certificates'][0]\
                        ['payload']['principal']['email']
            else:
                remote_host = config.get('auth.auth_url', 
                        'https://browserid.org/verify')
                post_data = urllib.urlencode({'assertion': assertion,
                    'audience': audience})
                rb = StringIO()
                curl = pycurl.Curl()
                curl.setopt(pycurl.URL, remote_host)
                curl.setopt(pycurl.FOLLOWLOCATION, 1)
                curl.setopt(pycurl.CONNECTTIMEOUT, 30)
                curl.setopt(pycurl.POST, 1)
                curl.setopt(pycurl.POSTFIELDS, post_data)
                curl.setopt(pycurl.WRITEFUNCTION, rb.write)
                try:
                    curl.perform()
                except Exception, e:
                    logger.error('Error verifying: %s' % repr(e))
                    return None
                curl.close()
                response = json.loads(rb.getvalue())
                if 'okay' in response.get('status'):
                    return response.get('email')
                return None

        except Exception, e:
            logger.info("Bad assertion [%s]" % repr(e))
            return None

    def _decode(self, dstr):
        try:
            return urlsafe_b64decode(self._check_b64pad(str(dstr)))
        except TypeError, e:
            logger.error("Decode Error %s [%s]" % (dstr, str(e)))
            return None

    def _check_b64pad(self, string):
        pad_size = 4 - (len(string) % 4)
        return string + ('=' * pad_size)

    def _parse_assertion(self, assertion):
        jwso = json.loads(self._decode(assertion))
        new_certs = []
        try:
            for cert in jwso['certificates']:
                (rhead, rpayload, rsig) = cert.split('.')
                new_certs.append({'head': json.loads(self._decode(rhead)),
                    'payload': json.loads(self._decode(rpayload)),
                    'sig': self._decode(rsig)})
            jwso['certificates'] = new_certs
            (rhead, rpayload, rsig) = jwso['assertion'].split('.')
            jwso['assertion'] = {'head': json.loads(self._decode(rhead)),
                    'payload': json.loads(self._decode(rpayload)),
                    'ig': self._decode(rsig)}
        except Exception, e:
            logger.error("Could not parse assertion [%s]" %  repr(e))
        return jwso
