import unittest2

from nose.tools import eq_

from bipostaldash.storage import configure_from_settings


class StorageTest(unittest2.TestCase):
    __test__ = False
    storage = None

    def test_resolve_alias(self):
        self.storage.add_alias('email', 'alias')
        eq_(self.storage.resolve_alias('alias'),
            {'email': 'email',
             'origin': '',
             'status': 'active',
             'alias': 'alias'})

    def test_resolve_alias_unknown_alias(self):
        # Return None when we try to resolve an unknown alias?
        eq_(self.storage.resolve_alias('404'), {})

    def test_add_alias(self):
        result = self.storage.add_alias('email', 'alias')
        result = self.storage.resolve_alias('alias')
        eq_(self.storage.resolve_alias('alias'),
            {'email': 'email',
             'status': 'active',
             'origin': '',
             'alias': 'alias'})
        result = self.storage.get_aliases('email')
        eq_(self.storage.get_aliases('email'),
            [{'alias': 'alias',
              'status': 'active',
              'origin': '',
              'email': 'email'}])

    def test_get_aliases(self):
        self.storage.add_alias('email', 'alias', origin='example.com')
        eq_(self.storage.get_aliases('email'),
            [{'alias': 'alias',
              'status': 'active',
              'origin': 'example.com',
              'email': 'email'}])

        self.storage.add_alias('email', 'alias2', origin='example.org')
        key = lambda x: x['alias']
        expected = [{'alias': 'alias2',
                     'status': 'active',
                     'origin': 'example.org',
                     'email': 'email'},
                    {'alias': 'alias',
                     'status': 'active',
                     'origin': 'example.com',
                     'email': 'email'}]
        eq_(sorted(self.storage.get_aliases('email'), key=key),
            sorted(expected, key=key))

    def test_get_aliases_fail_unkwown_email(self):
        # Default to [] when we try to get aliases for an unknown email.
        eq_(self.storage.get_aliases('email'), [])

    def test_delete_alias(self):
        self.storage.add_alias('email', 'alias')
        deleted = self.storage.delete_alias('email', 'alias')
        eq_(deleted, {'email': 'email', 'origin': '',
                      'alias': 'alias', 'status': 'deleted'})
        eq_(self.storage.resolve_alias('alias'), {})
        eq_(self.storage.get_aliases('email'), [])

    def test_delete_alias_unknown_alias(self):
        # No effect when we try to delete an unknown alias?
        self.storage.add_alias('email', 'alias')
        self.storage.delete_alias('email', 'alias2')
        eq_(self.storage.get_aliases('email'),
            [{'alias': 'alias', 'origin': '',
              'status': 'active', 'email': 'email'}])
        eq_(self.storage.resolve_alias('alias'),
            {'email': 'email', 'origin': '',
             'status': 'active', 'alias': 'alias'})

    def test_delete_alias_unknown_email(self):
        # No crash when we try to delete an unknown email.
        self.storage.delete_alias('email', 'alias')


class MemStorageTest(StorageTest):
    __test__ = True

    def setUp(self):
        settings = {'backend': 'bipostaldash.storage.mem.Storage'}
        self.storage = configure_from_settings('storage', settings)


class RedisStorageTest(StorageTest):
    __test__ = True

    def setUp(self):
        # Use a separate db for testing.

        settings = {'backend': 'bipostaldash.storage.redis_.Storage',
                    'db': 1,
                    'host': 'localhost',
                    'port': 6379,
                    }
        self.storage = configure_from_settings('storage', settings)
        # Clear out the db for testing.
        self.storage.redis.flushall()


class MysqlMemcacheTest(StorageTest):
    __test__ = True

    def setUp(self):
        settings = {'backend': 'bipostaldash.storage.mysql_memcache.Storage',
                    'mysql.user': 'rw',
                    'mysql.password': 'rw',
                    'mysql.host': 'localhost',
                    'mysql.user_db': 'bipostal.user',
                    'memcache.servers': 'localhost:11211'}
        self.storage = configure_from_settings('storage', settings)
        self.storage.flushall()
