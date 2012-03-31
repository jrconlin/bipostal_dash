import bipostaldash
import json
import mock
import os
import unittest2
import webtest
from bipostal.storage import mem
from bipostaldash import views
from nose.tools import eq_
from pyramid import httpexceptions as http
from pyramid import testing


class JSONRequest(testing.DummyRequest):

    def __init__(self, **kw):
        super(JSONRequest, self).__init__(**kw)
        if 'post' in kw:
            self.body = kw['post']

    @property
    def json_body(self):
        return json.loads(self.body, encoding=self.charset)


class DummyAuth(object):

    def set_dummy_return(self, response):
        self.response = response

    def get_user_id(self, request):
        return self.response


class ViewTest(unittest2.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        self.email = 'email@example.com'
        self.audience = 'example.com'
        self.alias = '123abc@example.com'
        self.config.testing_securitypolicy(userid=self.email, permissive=True)
        self.request = JSONRequest(post=json.dumps({'alias':
                self.alias,
            'audience': self.audience}))
        self.request.registry['storage'] = mem.Storage()
        # Default Auth:
        self.request.registry['auth'] = DummyAuth()
        self.request.registry['auth'].set_dummy_return(self.email)
        # Tested by test_oauth
        # self.request.registry['auth'] = bipostaldash.auth.oauth.OAuth()
        self.request.registry.settings['email_domain'] = 'browserid.org'

    def tearDown(self):
        testing.tearDown()

    def test_add_alias(self):
        response = views.add_alias(self.request)
        eq_(set(response.keys()), set(['email', 'alias', 'user', 'origin', 'status']))
        eq_(response['email'], self.email)

        eq_(views.list_aliases(self.request),
            {'email': self.email, 'aliases': [response]})

    def test_add_alias_from_body(self):
        request = JSONRequest(post=json.dumps({'alias': 'x@y.com',
            'audience': self.audience}))
        response = views.add_alias(request)
        eq_(response, {
                       'alias': 'x@y.com',
                       'status': 'active',
                       'email': self.email,
                       'user': self.email,
                       'origin': self.audience,
                       })

        eq_(views.list_aliases(self.request),
            {'email': self.email,
                'aliases': [{'email': self.email,
                          'user': self.email,
                          'origin': self.audience,
                          'alias': 'x@y.com',
                          'status': 'active'}]})

    def test_add_alias_from_body_bad_json(self):
        request = JSONRequest(post='not json')
        request.registry = self.request.registry
        with self.assertRaises(http.HTTPBadRequest):
            views.add_alias(request)

    def test_add_alias_from_body_bad_email(self):
        request = JSONRequest(post=json.dumps({'alias': 'x@y',
            'audience': self.audience}))
        request.registry = self.request.registry
        with self.assertRaises(http.HTTPBadRequest):
            views.add_alias(request)

    def test_get_alias(self):
        alias = views.add_alias(self.request)['alias']
        self.request.matchdict = {'alias': alias,
                'audience': self.audience}
        response = views.get_alias(self.request)
        eq_(response, {'email': self.email,
                       'user': self.email,
                       'alias': alias,
                       'origin': self.audience,
                       'status': 'active'})

    def test_list_aliases(self):
        alias1 = views.add_alias(self.request)
        # add second alias
        newbody = self.request.json_body
        newbody['alias'] = '456def@example.com'
        self.request.jsonbody = newbody
        self.request.body = json.dumps(newbody)
        alias2 = views.add_alias(self.request)
        response = views.list_aliases(self.request)
        eq_(response, {'email': self.email,
                       'aliases': [alias1, alias2],
                       })


    def test_alias_for_origin(self):
        alias1 = views.add_alias(self.request)
        self.request.matchdict = {'origin':
                self.audience}
        response = views.get_alias_for_origin(self.request)
        eq_(alias1, response.get('results')[0])
        self.request.matchdict = None
        

    def test_delete_alias(self):
        alias = views.add_alias(self.request)['alias']
        self.request.matchdict = {'alias': alias,
                'audience': self.audience}
        response = views.delete_alias(self.request)
        eq_(response, {'email': self.email,
                       'user': self.email,
                       'alias': alias,
                       'origin': self.audience,
                       'status': 'deleted'})
        self.request.matchdict = None
        eq_(views.list_aliases(self.request),
            {'email': self.email, 'aliases': []})

"""
    def test_change_alias(self):
        import pdb; pdb.set_trace()
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
"""


@mock.patch('bipostaldash.views.os.urandom')
def test_new_alias(urandom_mock):
    urandom_mock.return_value = ''.join(map(chr, [0, 1, 61, 62, 63, 64]))
    result_val = '01pqrs'
    request = JSONRequest(get="")
    request.environ['HTTP_HOST'] = 'browserid.org'
    #alias should be lower case, even if the urandom picked upper.
    eq_(views.new_alias(request),
            {'alias': '%s@browserid.org' % result_val})
    # Cornice currently faults on passing domain.
    request.environ['HTTP_HOST'] = 'woo.com'
    
    eq_(views.new_alias(request),
            {'alias': '%s@woo.com' % result_val})


class AppTest(unittest2.TestCase):

    def setUp(self):
        # Grab the development ini file.
        p = os.path
        ini = p.join(p.dirname(__file__), '../../etc/bipostaldash.ini')
        app = bipostaldash.main({'__file__': p.abspath(ini)})
        self.testapp = webtest.TestApp(app)

    def test_root(self):
        self.testapp.get('/', status=403)
