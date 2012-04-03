import logging
import os
import re
import string
import time

from bipostaldash.auth.default import DefaultAuth
from cornice import Service
from mako.template import Template
from pyramid import httpexceptions as http
from pyramid.response import Response

# Cornice currently renders JSON only. So only REST functions use it.
gen_alias = Service(name='new_alias', path='/new_alias/',
                    description='Return a new alias token')

aliases = Service(name='aliases', path='/alias/',
                  description='Manage the email <=> alias store.')

alias_detail = Service(name='alias-detail', path='/alias/{alias}',
                       description='Manage a single alias.')

origin = Service(name='origin', path='/origin/{origin}',
                    description='Fetch info for an origin')

user = Service(name='user', path='/user/', 
                  description='Get user info')

login_service = Service(name='login', path='/',
                    description='Login to service')

statics = Service(name='statics', path='/s/{cmd}',
                description='Catch-all semi-static services')

logger = logging.getLogger(__file__)


# Not the best; just make sure it looks like x@y.z.
EMAIL_RE = '[^@]+@[^.]+.\w+'


def default_domain(request):
    return request.environ.get('HTTP_HOST', 'browserid.org')


def make_alias(length=64, domain=None, prefix=None, **kw):
    chars = string.digits + string.lowercase
    base = len(chars)
    token = ''
    if prefix is not None:
        token = prefix
        length = length - len(prefix)
    token = token + (''.join(chars[ord(x) % base] for x in os.urandom(length)))
    token = token.lower()
    return '%s@%s' % (token, domain)


@gen_alias.get()
def new_alias(request, root=None, domain=None, prefix=None, **kw):
    params = dict(request.params.items())
    if (request.json_body):
        params = dict(params.items() + request.json_body.items())
    config = request.registry.get('config', {})
    if domain is None:
        domain = default_domain(request)
    if prefix is None:
        prefix = config.get('global.shard',None)
        if prefix is not None:
            prefix = str(prefix).rjust(config.get('global.shard_pad', 3), '0')
    reply = {'alias': make_alias(domain=domain, prefix=prefix)}
    if (params.get('callback')):
        reply['callback'] = params.get('callback')
    return reply

@aliases.get()
def list_aliases(request):
    db = request.registry['storage']
    auth = request.registry.get('auth', DefaultAuth)
    try:
        email = auth.get_user_id(request)
        if email is None:
            logger.error('No email found for list request.')
            raise http.HTTPUnauthorized()
        aliases = db.get_aliases(user=email) or []
        reply = {'email': email, 'aliases': aliases}
        if (request.params.get('callback')):
            reply['callback'] = request.params.get('callback')
        return reply
    except Exception, e:
        logger.error(repr(e))
        return http.HTTPForbidden()


@aliases.post()
def add_alias(request):
    db = request.registry['storage']
    auth = request.registry.get('auth', DefaultAuth)
    params = dict(request.params.items())
    if (request.json_body):
        params = dict(params.items() + request.json_body.items())
    try:
        email = auth.get_user_id(request)
    except Exception, e:
        logger.error(repr(e))
        raise http.HTTPUnauthorized()
    if email is None:
        logger.error('No email found for add alias')
        raise http.HTTPUnauthorized()
    alias = ''

    if request.body:
        try:
            alias = request.json_body.get('alias', None)
            audience = request.json_body.get('audience', None)
            if alias is None:
                alias = new_alias(request, 
                        domain=audience).get('alias')
            if audience is None and '@' in alias:
                (token, audience) = alias.split('@')
            if alias is None and audience is not None:
                alias = make_alias(domain=audience)
        except Exception, e:
            logging.error(repr(e))
            raise http.HTTPBadRequest()
    if not re.match(EMAIL_RE, alias) or db.resolve_alias(alias):
        raise http.HTTPBadRequest()

    reply = db.add_alias(email=email, user=email, 
            alias=alias, origin=audience)
    logger.info('New alias for %s.', email)
    if (params.get('callback')):
        reply['callback'] = params.get('callback')
    return reply


@alias_detail.get()
def get_alias(request):
    """Get the real address for a given alias."""
    db = request.registry['storage']
    alias = request.matchdict['alias']
    audience = request.matchdict.get('audience')
    if audience is None and '@' in alias:
        (token, audience) = alias.split('@')
    reply = db.resolve_alias(alias=alias, origin=audience)
    if (request.params.get('callback')):
        reply['callback'] = request.params.get('callback')
    return reply


@alias_detail.delete()
def delete_alias(request):
    """Delete an alias."""
    auth = request.registry.get('auth', DefaultAuth)
    try:
        email = auth.get_user_id(request)
    except Exception, e:
        logging.error(repr(e))
        raise http.HTTPUnauthorized()
    db = request.registry['storage']
    alias = request.matchdict['alias']
    audience = None;
    if 'audience' in request.matchdict:
        audience = request.matchdict['audience']
    reply = db.delete_alias(user=email, alias=alias, origin=audience)
    logger.info('Deleting alias for %s.', email)
    if (request.params.get('callback')):
        reply['callback'] = request.params.get('callback')
    return reply


@alias_detail.put()
def change_alias(request):
    """Make a change to an existing alias."""
    params = dict(request.params.items())
    if (request.json_body):
        params = dict(params.items() + request.json_body.items())
    try:
        status = request.json_body['status']
        if (status not in ('active', 'inactive', 'deleted')):
            logging.error("Invalid status specified")
            raise http.HTTPBadRequest()
    except Exception, e:
        logging.error(repr(e))
        raise http.HTTPBadRequest()
    auth = request.registry.get('auth', DefaultAuth)
    try:
        email = auth.get_user_id(request)
    except Exception, e:
        logging.error(repr(e))
        return http.HTTPForbidden()
    db = request.registry['storage']
    alias = request.matchdict['alias']
    reply = db.set_status_alias(user=email, alias=alias, status=status)
    if (params.get('callback')):
        reply['callback'] = params.get('callback')
    return reply


@origin.get()
def get_alias_for_origin(request):
    """ Get the aliases for a user for an origin """
    try:
        auth = request.registry.get('auth', DefaultAuth)
        email = auth.get_user_id(request)
    except Exception, e:
        logging.error(repr(e))
        raise http.HTTPUnauthorized()
    db = request.registry['storage']
    origin = request.matchdict['origin']
    reply = {'results': db.get_alias_for_origin(user=email, 
            origin=origin)}
    if (request.params.get('callback')):
        reply['callback'] = request.params.get('callback')
    return reply


def _gen_keys(auth, config):
    """ Generate and register the oauth keys for this user """
    # build the keys from the token generator
    return auth.gen_keys(access=make_alias().split('@')[0],
            secret=make_alias().split('@')[0],
            refresh=make_alias().split('@')[0],
            config=config)


@login_service.delete()
def logout(request):
    """ Log the user out """
    reply = {'status': False}
    try:
        session = request.session
        auth = request.registry.get('dash_auth', DefaultAuth)
        email = auth.get_user_id(request)
        if email:
            session['uid'] = None
            session['keys'] = None
            session.save()
            reply = {'staus': True }
    except Exception, e:
        logging.error(repr(e))
    if (request.params.get('callback')):
        reply['callback'] = request.params.get('callback')
    return reply

@login_service.get()
@login_service.post()
def login(request):
    """ Accept the browserid auth element """
    params = dict(request.params.items())
    try:
        if (request.json_body):
            params = dict(params.items() + request.json_body.items())
    except ValueError:
        # there was no json body. Pass.
        pass
    try:
        session = request.session
        config = request.registry.get('config', {})
        # Use a different auth mechanism for user login.
        login_auth = request.registry.get('dash_auth', DefaultAuth())
        auth = request.registry.get('auth', DefaultAuth)
        email = login_auth.get_user_id(request)
        if email is None:
            template = Template(filename=os.path.join('bipostaldash',
                'templates', 'login.mako'))
            response = Response(str(template.render()),
                    status=403)
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
    if session.get('keys') is None:
        keys = _gen_keys(auth=auth, config=config)
        logger.info('logging user in, creating keys. %s  ' %
            repr(keys))
        session['keys'] = keys
    if 'javascript' in request.response.content_type:
        response = session.get('keys');
        if (request.params.get('callback')):
            response['callback'] = request.params.get('callback')
    else:
        template = Template(filename=os.path.join('bipostaldash',
                'templates', 'mainpage.mako'))
        response = Response(str(template.render(user=email,
                    keys=session.get('keys'),
                    request=request)))
    # set the beakerid
    session['uid'] = email
    session.save()
    return response

@user.get()
def get_user(request):
    auth = request.registry.get('dash_auth', DefaultAuth())
    email = auth.get_user_id(request)
    if email is None:
        return http.HTTPForbidden()
    db = request.registry['storage']
    reply = db.get_user(email)
    if (request.params.get('callback')):
        reply['callback'] = request.params.get('callback')
    return reply

@user.post()
def update_user(request):
    try:
        auth = request.registry.get('dash_auth', DefaultAuth())
        email = auth.get_user_id(request)
        alias = request.json_body.get('alias', email)
        metainfo = request.json_body.get('metainfo', None)
        params = dict(request.params.items())
        if (request.json_body):
            params = dict(params.items() + request.json_body.items())
        if email is None:
            return http.HTTPForbidden()
        db = request.registry['storage']
        user_info = db.get_user(email)
        metainfo = user_info.get('metainfo', {}).update(metainfo)
        reply = db.create_user(email, alias, metainfo)
        if (params.get('callback')):
            reply['callback'] = params.get('callback')
        return reply
    except Exception, e:
        logger.error('Could not update record: [%s]' % repr(e))
        raise


# statics
def stime(request):
    reply = {'time': int(time.time())}
    if (request.params.get('callback')):
        reply['callback'] = request.params.get('callback')
    return reply


def worker(request):
    session = request.session
    config = request.registry.get('config', {})
    if (session.get('uid')):
        template = Template(filename=os.path.join('bipostaldash',
                'templates', 'worker.mako'))
        response = Response(str(template.render(session=session,
                config=config,
                request=request)))
        return response
    raise http.HTTPForbidden()


@statics.get()
def statics(request):
    cmds = {'time': stime,
            'worker': worker}
    cmd = request.matchdict.get('cmd')
    if cmd in cmds:
        cmd = cmds.get(cmd)
        return cmd(request)
    raise http.HTTPNotFound()


