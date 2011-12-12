import logging
import os
import re
import string

from pyramid import httpexceptions as http
from pyramid.response import Response
from bipostaldash.auth.default import DefaultAuth
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
    email = auth.get_user_id(request)
    if email is None:
        return http.HTTPForbidden()
    aliases = db.get_aliases(user=email) or []
    return {'email': email, 'aliases': aliases}


@aliases.post()
def add_alias(request):
    db = request.registry['storage']
    auth = request.registry.get('auth', DefaultAuth)
    email = auth.get_user_id(request)
    if email is None:
        return http.HTTPForbidden()
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
    email = auth.get_user_id(request)
    db = request.registry['storage']
    alias = request.matchdict['alias']
    rv = db.delete_alias(email=email, alias=alias)
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
    email = auth.get_user_id(request)
    db = request.registry['storage']
    alias = request.matchdict['alias']
    rv = db.add_alias(email=email, alias=alias, status=active)
    return rv

@login_service.get()
@login_service.post()
def login(request):
    """ Accept the browserid auth element """
    try:
        session = request.session
        # Use a different auth mechanism for user login.
        auth = request.registry.get('dash_auth', DefaultAuth)
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
    template = Template(filename = os.path.join('bipostaldash',
            'templates', 'mainpage.mako'))
    response = Response(str(template.render(user = email,
                    request = request)))
    # set the beakerid
    session['uid'] = email
    session.save()
    return response


