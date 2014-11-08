import unittest
import os
from mock import *
import ldap
from StringIO import StringIO

from edir_reminder_service.tests.base import LocalLDAPTests
import edir_reminder_service.config
from edir_reminder_service_main import main
import edir_reminder_service.globals as g

class TestConnection(LocalLDAPTests):
    @patch('sys.stdout', new_callable=StringIO)
    @patch('sys.stderr', new_callable=StringIO)
    def test_10_connect(self, mock_stderr, mock_stdout):
        rc = main(['-c', os.path.dirname(__file__) + "/password.conf"])
        self.assertEqual(mock_stderr.getvalue(), '')
        self.assertEqual(rc, 0)

        self.assertEquals(self.ldapobj.methods_called(), ['initialize', 'simple_bind_s', 'search_s'])
        #self.assertEquals(sorted(results), sorted([self.manager, self.alice]))

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestConnection)
    unittest.TextTestRunner(verbosity=9).run(suite)
