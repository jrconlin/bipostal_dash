import json
import os
import unittest2

import mock
import webtest
from pyramid import testing
from pyramid import httpexceptions as http
from nose.tools import eq_

from bipostaldash.storage import mem
from bipostaldash import views
import bipostaldash

class JSONRequest(testing.DummyRequest):

    def __init__(self, **kw):
        super(JSONRequest, self).__init__(**kw)
        if 'post' in kw:
            self.body = kw['post']

    @property
    def json_body(self):
        return json.loads(self.body, encoding=self.charset)


class ViewTest(unittest2.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        self.email = 'email@foo.com'
        self.config.testing_securitypolicy(userid=self.email, permissive=True)
        self.request = testing.DummyRequest()
        self.request.registry['storage'] = mem.Storage()
        # Default Auth:
        # self.request.registry['auth'] = DummyAuth()
        # Tested by test_oauth
        # self.request.registry['auth'] = bipostaldash.auth.oauth.OAuth()
        self.request.registry.settings['email_domain'] = 'browserid.org'

    def tearDown(self):
        testing.tearDown()

    def test_add_alias(self):
        response = views.add_alias(self.request)
        eq_(set(response.keys()), set(['email', 'alias', 'origin', 'status']))
        eq_(response['email'], self.email)

        eq_(views.list_aliases(self.request),
            {'email': self.email, 'aliases': [response]})

    def test_add_alias_from_body(self):
        request = JSONRequest(post=json.dumps({'alias': 'x@y.com'}))
        response = views.add_alias(request)
        eq_(response, {'email': self.email,
                       'origin': '',
                       'alias': 'x@y.com',
                       'status': 'active'})

        eq_(views.list_aliases(self.request),
            {'email': self.email,
             'aliases': [{'email': self.email,
                          'origin': '',
                          'alias': 'x@y.com',
                          'status': 'active'}]})

    def test_add_alias_from_body_dupe(self):
        request = JSONRequest(post=json.dumps({'alias': 'x@y.com'}))
        views.add_alias(request)

        # Calling it again will fail the dupe check.
        with self.assertRaises(http.HTTPBadRequest):
            views.add_alias(request)

    def test_add_alias_from_body_bad_json(self):
        request = JSONRequest(post='not json')
        with self.assertRaises(http.HTTPBadRequest):
            views.add_alias(request)

    def test_add_alias_from_body_bad_email(self):
        request = JSONRequest(post=json.dumps({'alias': 'x@y'}))
        with self.assertRaises(http.HTTPBadRequest):
            views.add_alias(request)

    def test_get_alias(self):
        alias = views.add_alias(self.request)['alias']
        self.request.matchdict = {'alias': alias}
        response = views.get_alias(self.request)
        eq_(response, {'email': self.email,
                       'alias': alias,
                       'origin': '',
                       'status': 'active'})

    def test_list_aliases(self):
        alias1 = views.add_alias(self.request)
        alias2 = views.add_alias(self.request)
        response = views.list_aliases(self.request)
        eq_(response, {'email': self.email,
                       'aliases': [alias1, alias2],
                       })

    def test_delete_alias(self):
        alias = views.add_alias(self.request)['alias']
        self.request.matchdict = {'alias': alias}
        response = views.delete_alias(self.request)
        eq_(response, {'email': self.email,
                       'alias': alias,
                       'origin': '',
                       'status': 'deleted'})
        self.request.matchdict = None
        eq_(views.list_aliases(self.request),
            {'email': self.email, 'aliases': []})

    def test_change_alias(self):
        alias = views.add_alias(self.request)['alias']
        ## WTF is this doing?
        request = JSONRequest(post=json.dumps({'status': 'deleted'}))
        request.matchdict = {'alias': alias}
        response = views.change_alias(request)
        eq_(response, {'email': self.email,
                       'origin': '',
                       'alias': alias,
                       'status': 'deleted'})

        request = JSONRequest(post=json.dumps({'status': 'active'}))
        request.matchdict = {'alias': alias}
        response = views.change_alias(request)
        eq_(response, {'email': self.email,
                       'origin': '',
                       'alias': alias,
                       'status': 'active'})


@mock.patch('bipostaldash.views.os.urandom')
def test_new_alias(urandom_mock):
    urandom_mock.return_value = ''.join(map(chr, [0, 1, 61, 62, 63, 64]))
    request = JSONRequest(get="")
    request.environ['HTTP_HOST'] = 'browserid.org'
    eq_(views.new_alias(request), 
            '01Z012@browserid.org')
    eq_(views.new_alias(request, domain='woo.com'), 
            '01Z012@woo.com')


class AppTest(unittest2.TestCase):


    def setUp(self):
        # Grab the development ini file.
        p = os.path
        ini = p.join(p.dirname(__file__), '../../etc/bipostaldash-dev.ini')
        app = bipostaldash.main({'__file__': p.abspath(ini)})
        self.testapp = webtest.TestApp(app)

    def test_root(self):
        self.testapp.get('/', status=403)

