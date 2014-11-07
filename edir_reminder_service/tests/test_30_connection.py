import unittest
from edir_reminder_service.tests.base import FakeLDAPTests

class TestConnection(FakeLDAPTests):
    def test_10_bla(self):
        pass

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestConnection)
    unittest.TextTestRunner(verbosity=2).run(suite)