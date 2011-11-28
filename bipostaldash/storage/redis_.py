import redis


class Storage(object):
    aliases = 'aliases:2:%s-%s'
    emails = 'emails:2:%s'

    def __init__(self, **kw):
        self.redis = redis.Redis(**kw)

    def resolve_alias(self, alias, origin=''):
        #Handle special cases where the origin is already included
        if '-' in alias and origin is '':
            (alias, origin) = alias.split('-', 1)

        data = self.redis.hgetall(self.aliases  % (alias, origin))
        if data:
            data['status'] = data['status'].lower()
            data.update(alias=alias)
        return data

    def add_alias(self, email, alias, origin='', status='active'):
        rv = {'email': email, 'origin': origin, 'status': status}
        self.redis.hmset(self.aliases % (alias, origin), rv)
        self.redis.sadd(self.emails % email, '%s-%s' % (alias, origin))
        return self.resolve_alias(alias)

    def get_aliases(self, email):
        # XXX: this makes N redis calls, one per alias.
        aliases = self.redis.smembers(self.emails % email)
        return map(self.resolve_alias, aliases)

    def delete_alias(self, email, alias, origin=''):
        self.redis.delete(self.aliases % (alias, origin))
        self.redis.srem(self.emails % email, '%s-%s' % (alias, origin))
        return {'email': email,
                'alias': alias,
                'origin': origin,
                'status': 'deleted'}
