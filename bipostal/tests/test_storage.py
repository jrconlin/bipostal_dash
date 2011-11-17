import unittest2

from nose.tools import eq_

from bipostal.storage import configure_from_settings


class StorageTest(unittest2.TestCase):
    __test__ = False
    storage = None

    def test_resolve_alias(self):
        self.storage.add_alias('email', 'alias')
        eq_(self.storage.resolve_alias('alias'),
            {'email': 'email', 'active': True, 'alias': 'alias'})

    def test_resolve_alias_unknown_alias(self):
        # Return None when we try to resolve an unknown alias?
        eq_(self.storage.resolve_alias('404'), {})

    def test_add_alias(self):
        self.storage.add_alias('email', 'alias')
        eq_(self.storage.resolve_alias('alias'),
            {'email': 'email', 'active': True, 'alias': 'alias'})
        eq_(self.storage.get_aliases('email'),
            [{'alias': 'alias', 'active': True, 'email': 'email'}])

    def test_get_aliases(self):
        self.storage.add_alias('email', 'alias')
        eq_(self.storage.get_aliases('email'),
            [{'alias': 'alias', 'active': True, 'email': 'email'}])

        self.storage.add_alias('email', 'alias2')
        key = lambda x: x['alias']
        expected = [{'alias': 'alias2', 'active': True, 'email': 'email'},
                    {'alias': 'alias', 'active': True, 'email': 'email'}]
        eq_(sorted(self.storage.get_aliases('email'), key=key),
            sorted(expected, key=key))

    def test_get_aliases_fail_unkwown_email(self):
        # Default to [] when we try to get aliases for an unknown email.
        eq_(self.storage.get_aliases('email'), [])

    def test_delete_alias(self):
        self.storage.add_alias('email', 'alias')
        deleted = self.storage.delete_alias('email', 'alias')
        eq_(deleted, {'email': 'email', 'alias': 'alias', 'active': False})
        eq_(self.storage.resolve_alias('alias'), {})
        eq_(self.storage.get_aliases('email'), [])

    def test_delete_alias_unknown_alias(self):
        # No effect when we try to delete an unknown alias?
        self.storage.add_alias('email', 'alias')
        self.storage.delete_alias('email', 'alias2')
        eq_(self.storage.get_aliases('email'),
            [{'alias': 'alias', 'active': True, 'email': 'email'}])
        eq_(self.storage.resolve_alias('alias'),
            {'email': 'email', 'active': True, 'alias': 'alias'})

    def test_delete_alias_unknown_email(self):
        # No crash when we try to delete an unknown email.
        self.storage.delete_alias('email', 'alias')


class MemStorageTest(StorageTest):
    __test__ = True

    def setUp(self):
        settings = {'backend': 'bipostal.storage.mem.Storage'}
        self.storage = configure_from_settings('storage', settings)


class RedisStorageTest(StorageTest):
    __test__ = True

    def setUp(self):
        # Use a separate db for testing.
        settings = {'backend': 'bipostal.storage.redis_.Storage', 'db': 1}
        self.storage = configure_from_settings('storage', settings)
        # Clear out the db for testing.
        self.storage.redis.flushall()
