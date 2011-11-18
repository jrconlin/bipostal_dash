class Storage(object):

    def __init__(self, **kw):
        self.db = {}

    def resolve_alias(self, alias):
        return self.db.get(alias, {})

    def add_alias(self, email, alias, active=True):
        self.db[alias] = rv = {'email': email, 'active': active,
                               'alias': alias}
        self.db.setdefault(email, []).append(alias)
        return rv

    def get_aliases(self, email):
        return map(self.resolve_alias, self.db.get(email, []))

    def delete_alias(self, email, alias):
        if alias in self.db:
            del self.db[alias]
            self.db[email].remove(alias)
        return {'email': email, 'alias': alias, 'active': False}
