import unittest

from pyramid import testing


class ViewTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def test_user_info_service(self):
        from bipostal.views import get_info, set_info
        request = testing.DummyRequest()
        request.matchdict = {"username": "user1"}
        info = get_info(request)
        self.assertEqual(info, {})
