import logging
import os
import re
import string

from pyramid import httpexceptions as http
from pyramid.security import authenticated_userid

from cornice import Service

gen_alias = Service(name='new_alias', path='/new_alias/',
                    description='Return a new alias token')

aliases = Service(name='aliases', path='/alias/',
                  description='Manage the email <=> alias store.')

alias_detail = Service(name='alias-detail', path='/alias/{alias}',
                       description='Manage a single alias.')


logger = logging.getLogger(__file__)

# Not the best; just make sure it looks like x@y.z.
EMAIL_RE = '[^@]+@[^.]+.\w+'


def make_alias(length=64, domain='browserid.org'):
    chars = string.digits + string.letters
    base = len(chars)
    token = ''.join(chars[ord(x) % base] for x in os.urandom(length))
    return '%s@%s' % (token, domain)


@gen_alias.get()
def new_alias(request=None, domain='browserid.org'):
    return make_alias(domain=domain)


@aliases.get(permission='authenticated')
def list_aliases(request):
    db = request.registry['storage']
    auth  = request.registry.get('auth', authenticated_userid)
    email = auth.get_user_id(request)
    aliases = db.get_aliases(email=email) or []
    return {'email': email, 'aliases': aliases}


@aliases.post(permission='authenticated')
def add_alias(request):
    db = request.registry['storage']
    auth  = request.registry.get('auth', authenticated_userid)
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
    auth = request.registry.get('auth', authenticated_userid)
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
    auth  = request.registry.get('auth', authenticated_userid)
    email = auth.get_user_id(request)
    db = request.registry['storage']
    alias = request.matchdict['alias']
    rv = db.add_alias(email=email, alias=alias, status=active)
    return rv
