import logging
import urllib2
import browserid 


class BrowserIDAuth(object):

    _raw_assertion = None

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
            assertion = self._raw_assertion
            if assertion is None:
                return None
        try:
            data = browserid.verify(assertion, audience)
            return data['email']
        except Exception, e:
            logging.info("Bad assertion [%s]" % repr(e))
            return None
