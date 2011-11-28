class Storage(object):

    def __init__(self, **kw):
        self.db = {}

    def resolve_alias(self, alias, origin=''):
        return self.db.get("%s-%s" % (alias, origin), {})

    def add_alias(self, email, alias, origin='', status='active'):
        self.db["%s-%s" % (alias,origin)] = rv = {'email': email,
                               'status': status,
                               'origin': origin,
                               'alias': alias}
        self.db.setdefault(email, []).append("%s-%s" % (alias, origin))
        return rv

    def get_aliases(self, email):
        result = []
        aliases = self.db.get(email, [])
        for alias in aliases:
            elem = alias.split('-',1)
            result.append(self.resolve_alias(alias=elem[0], origin=elem[1]))
        return result

    def delete_alias(self, email, alias, origin=''):
        if "%s-%s" % (alias, origin) in self.db:
            del self.db["%s-%s" % (alias, origin)]
            self.db[email].remove("%s-%s" % (alias, origin))
        return {'email': email,
                'alias': alias,
                'origin': origin,
                'status': 'deleted'}
