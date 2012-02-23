from pyramid.security import authenticated_userid
import time

class DefaultAuth(object):

    def get_user_id(self, request):
        return authenticated_userid(request)


class DefaultKeyStore(object):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(DefaultKeyStore,
                    cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self, **kwargs):
        self.exp = [None for i in range(0, 200)]
        self.store = {}

    def add(self, key, data):
        nuke = self.exp.pop(0)
        if nuke is not None:
            del self.store[self.exp.pop(0)]
        self.exp.append(key)
        self.store[key] = data

    def get(self, key):
        return self.store.get(key)

    def get_keys(self, request):
        return request.session.get('keys', None)

    def gen_keys(self, access, secret, config, **kw):
        return {
                'token_type': 'none',
                'access_token': access,
                'server_time': int(time.time()),
                }
                
