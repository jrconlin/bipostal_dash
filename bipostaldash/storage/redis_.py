import redis


class Storage(object):
    aliases = 'aliases:2:'
    emails = 'emails:2:'

    def __init__(self, **kw):
        self.redis = redis.Redis(**kw)

    def resolve_alias(self, alias):
        data = self.redis.hgetall(self.aliases + alias)
        if data:
            data['active'] = bool(int(data['active']))
            data.update(alias=alias)
        return data

    def add_alias(self, email, alias, active=True):
        rv = {'email': email, 'active': int(active)}
        self.redis.hmset(self.aliases + alias, rv)
        self.redis.sadd(self.emails + email, alias)
        return self.resolve_alias(alias)

    def get_aliases(self, email):
        # XXX: this makes N redis calls, one per alias.
        aliases = self.redis.smembers(self.emails + email)
        return map(self.resolve_alias, aliases)

    def delete_alias(self, email, alias):
        self.redis.delete(self.aliases + alias)
        self.redis.srem(self.emails + email, alias)
        return {'email': email, 'alias': alias, 'active': False}
