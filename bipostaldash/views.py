import logging
import os
import re
import string

from pyramid import httpexceptions as http
from bipostaldash.auth.default import DefaultAuth

from cornice import Service

gen_alias = Service(name='new_alias', path='/new_alias/',
                    description='Return a new alias token')

login_service  = Service(name='login', path='/login/',
                    description='Login to service')

aliases = Service(name='aliases', path='/alias/',
                  description='Manage the email <=> alias store.')

alias_detail = Service(name='alias-detail', path='/alias/{alias}',
                       description='Manage a single alias.')


logger = logging.getLogger(__file__)

# Not the best; just make sure it looks like x@y.z.
EMAIL_RE = '[^@]+@[^.]+.\w+'

def default_domain(request):
    return request.environ.get('HTTP_HOST')


def make_alias(length=64, domain=None):
    chars = string.digits + string.letters
    base = len(chars)
    token = ''.join(chars[ord(x) % base] for x in os.urandom(length))
    return '%s@%s' % (token, domain)


@gen_alias.get()
def new_alias(request=None, root=None, domain=None):
    if domain is None:
        domain = default_domain(request)
    return make_alias(domain=domain)


@aliases.get(permission='authenticated')
def list_aliases(request):
    db = request.registry['storage']
    auth = request.registry.get('auth', DefaultAuth)
    #email = auth.get_user_id(request)
    email = auth.get_user_id(request)
    aliases = db.get_aliases(email=email) or []
    return {'email': email, 'aliases': aliases}


@aliases.post(permission='authenticated')
def add_alias(request):
    db = request.registry['storage']
    auth = request.registry.get('auth', DefaultAuth)
    email = auth.get_user_id(request)

    if request.body:
        try:
            alias = request.json_body['alias']
        except Exception:
            raise http.HTTPBadRequest()
    else:
        alias = new_alias(domain=request.registry.settings['email_domain'])
    if not re.match(EMAIL_RE, alias) or db.resolve_alias(alias):
        raise http.HTTPBadRequest()

    rv = db.add_alias(email=email, alias=alias)
    logger.info('New alias for %s.', email)
    return rv


@alias_detail.get()
def get_alias(request):
    """Get the real address for a given alias."""
    db = request.registry['storage']
    alias = request.matchdict['alias']
    rv = db.resolve_alias(alias=alias)
    return rv


@alias_detail.delete(permission='authenticated')
def delete_alias(request):
    """Delete an alias."""
    auth = request.registry.get('auth', DefaultAuth)
    email = auth.get_user_id(request)
    db = request.registry['storage']
    alias = request.matchdict['alias']
    rv = db.delete_alias(email=email, alias=alias)
    logger.info('Deleting alias for %s.', email)
    return rv


@alias_detail.post(permission='authenticated')
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

@login_service.post()
@login_service.get()
def login(request):
    """ Accept the browserid auth element """
    try:
        # Use a different auth mechanism for user login.
        import pdb; pdb.set_trace()
        auth = request.registry.get('dash_auth', DefaultAuth)
        email = auth.get_user_id(request)
        if email is None:
            raise http.HTTPSeeOther(location = "/login.html")
        db = request.registry['storage']
        db.create_user(email=email)
        # set the beakerid
    except Exception, e:
        logging.info('Invalid or missing credentials [%s]' % repr(e))
        raise http.HTTPUnauthorized()
    return list_aliases(request)
