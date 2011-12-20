import logging
import os
import re
import string

from pyramid import httpexceptions as http
from pyramid.response import Response
from bipostaldash.auth.default import DefaultAuth
from bipostaldash.auth.default import DefaultKeyStore
from mako.template import Template


from cornice import Service

# Cornice currently renders JSON only. So only REST functions use it.
gen_alias = Service(name='new_alias', path='/new_alias/',
                    description='Return a new alias token')

aliases = Service(name='aliases', path='/alias/',
                  description='Manage the email <=> alias store.')

alias_detail = Service(name='alias-detail', path='/alias/{alias}',
                       description='Manage a single alias.')

login_service  = Service(name='login', path='/',
                    description='Login to service')


logger = logging.getLogger(__file__)



# Not the best; just make sure it looks like x@y.z.
EMAIL_RE = '[^@]+@[^.]+.\w+'

def default_domain(request):
    return request.environ.get('HTTP_HOST', 'browserid.org')


def make_alias(length=64, domain=None):
    chars = string.digits + string.letters
    base = len(chars)
    token = ''.join(chars[ord(x) % base] for x in os.urandom(length))
    return '%s@%s' % (token, domain)


@gen_alias.get()
def new_alias(request, root=None, domain=None):
    if domain is None:
        domain = default_domain(request)
    return make_alias(domain=domain)

@aliases.get()
def list_aliases(request):
    db = request.registry['storage']
    auth = request.registry.get('auth', DefaultAuth)
    try:
        email = auth.get_user_id(request)
        if email is None:
            raise http.HTTPUnauthorized()
        aliases = db.get_aliases(user=email) or []
        return {'email': email, 'aliases': aliases}
    except Exception, e:
        return http.HTTPForbidden()


@aliases.post()
def add_alias(request):
    db = request.registry['storage']
    auth = request.registry.get('auth', DefaultAuth)
    try:
        email = auth.get_user_id(request)
    except Exception, e:
        raise http.HTTPUnauthorized()
    if email is None:
        raise http.HTTPUnauthorized()
    alias = ''

    if request.body:
        try:
            alias = request.json_body['alias']
        except Exception:
            raise http.HTTPBadRequest()
    else:
        alias = make_alias(domain=request.registry.settings['email_domain'])
    if not re.match(EMAIL_RE, alias) or db.resolve_alias(alias):
        raise http.HTTPBadRequest()

    rv = db.add_alias(user=email, alias=alias)
    logger.info('New alias for %s.', email)
    return rv


@alias_detail.get()
def get_alias(request):
    """Get the real address for a given alias."""
    db = request.registry['storage']
    alias = request.matchdict['alias']
    rv = db.resolve_alias(alias=alias)
    return rv


@alias_detail.delete()
def delete_alias(request):
    """Delete an alias."""
    auth = request.registry.get('auth', DefaultAuth)
    try:
        email = auth.get_user_id(request)
    except Exception:
        raise http.HTTPUnauthorized()
    db = request.registry['storage']
    alias = request.matchdict['alias']
    rv = db.delete_alias(user=email, alias=alias)
    logger.info('Deleting alias for %s.', email)
    return rv


@alias_detail.post()
def change_alias(request):
    """Make a change to an existing alias."""
    try:
        active = request.json_body['status']
    except Exception:
        raise http.HTTPBadRequest()
    auth = request.registry.get('auth', DefaultAuth)
    try:
        email = auth.get_user_id(request)
    except Exception:
        return http.HTTPForbidden()
    db = request.registry['storage']
    alias = request.matchdict['alias']
    rv = db.add_alias(user=email, alias=alias, status=active)
    return rv

def _gen_keys(config):
    """ Generate and register the oauth keys for this user """
    # build the keys from the token generator
    result = {
            'consumer_key': make_alias().split('@')[0],
            'shared_secret': make_alias().split('@')[0]
            }
    #stuff them into redis for lookup and auth.
    return result

@login_service.get()
@login_service.post()
def login(request):
    """ Accept the browserid auth element """
    try:
        session = request.session
        # Use a different auth mechanism for user login.
        auth = request.registry.get('dash_auth', DefaultAuth)
        key_store = request.registry.get('key_store', DefaultKeyStore)
        email = auth.get_user_id(request)
        if email is None:
            template = Template(filename = os.path.join('bipostaldash',
                'templates', 'login.mako'))
            response = Response(str(template.render()),
                    status = 403)
            if (session.get('uid')):
                del(session['uid'])
            session.persist()
            session.save()
            return response
        db = request.registry['storage']
        db.create_user(user=email)
    except Exception, e:
        logging.info('Invalid or missing credentials [%s]' % repr(e))
        raise http.HTTPUnauthorized()
    keys = _gen_keys(config=request.registry.get('config'))
    logger.info('logging user in, creating keys. %s : %s' % 
            (keys['consumer_key'], keys['shared_secret']))
    key_store.add(keys['consumer_key'], keys['shared_secret'])
    if 'javascript' in request.response.content_type:
        response = {'consumer_key': 
                    keys.get('consumer_key'),
                    'shared_secret': 
                    keys.get('shared_secret')}
    else:
        template = Template(filename = os.path.join('bipostaldash',
                'templates', 'mainpage.mako'))
        response = Response(str(template.render(user = email,
                    keys = keys,
                    request = request)))

    # set the beakerid
    session['uid'] = email
    session.save()
    return response


