from services import logger
from base64 import urlsafe_b64decode
import urllib2
import json
import urllib2


class BrowserIDAuth(object):

    def __init__(self, 
            auth_server='browserid.org', 
            **kw):
        self._server = auth_server

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
            audience = self._server
        if assertion is None:
            assertion = request.params.get('assertion')
        if assertion is None:
            return None
        try:
            #note: this does not validate the assertion (yet).
            # Still need to pull the public key from the server
            assertion = str(urllib2.unquote(assertion)).strip()
            parsed_cert = self._parse_assertion(assertion)
            return parsed_cert['certificates'][0]\
                    ['payload']['principal']['email']
        except Exception, e:
            logger.info("Bad assertion [%s]" % repr(e))
            return None

    def _decode(self, dstr):
        try:
            return urlsafe_b64decode(self._check_b64pad(str(dstr)))
        except TypeError, e:
            logger.error("Decode Error %s [%s]" % (dstr, str(e)))

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
