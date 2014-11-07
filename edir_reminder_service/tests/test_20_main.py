import unittest
import os
from mock import *
from StringIO import StringIO

import edir_reminder_service.config
from edir_reminder_service_main import main
import edir_reminder_service.globals as g

class TestMain(unittest.TestCase):
    
    @patch('sys.stdout', new_callable=StringIO)
    @patch('sys.stderr', new_callable=StringIO)
    def test_010_shows_help(self, mock_stderr, mock_stdout):
        rc = main(['--help'])
        self.assertTrue(mock_stdout.getvalue().startswith('Usage: edir-reminder-service [OPTION]...'), [mock_stdout.getvalue()[:40], 'Usage: edir-reminder-service [OPTIONS]'])
        self.assertEqual(rc, 0)
        
    @patch('sys.stdout', new_callable=StringIO)
    @patch('sys.stderr', new_callable=StringIO)
    def test_020_shows_help_even_after_other_arguments(self, mock_stderr, mock_stdout):
        rc = main(['-v', '--test', 'foo@localhost', '--help', '-d'])
        self.assertTrue(mock_stdout.getvalue().startswith('Usage: edir-reminder-service [OPTION]...'), [mock_stdout.getvalue()[:40], 'Usage: edir-reminder-service [OPTIONS]'])
        self.assertEqual(rc, 0)
        
    def test_020_reject_unknown_parameters(self):
        rc = main(['--foo'])
        self.assertEqual(rc, 2)

    @patch('edir_reminder_service_main.run')
    def test_030_main_reject_non_option_args(self, mock_run):
        rc = main(['foo'])
        self.assertEqual(rc, 2)
        self.assertFalse(mock_run.called)

    @patch('edir_reminder_service_main.run')
    def test_030_main_does_not_run_without_config(self, mock_run):
        rc = main([])
        self.assertEqual(rc, 2)
        self.assertFalse(mock_run.called)

    @patch('edir_reminder_service_main.run')
    def test_040_main_sets_globals(self, mock_run):
        rc = main(['-c', os.path.dirname(__file__) + "/password.conf"])
        self.assertTrue(mock_run.called)
        self.assertEqual(g.DEBUG, 0)
        self.assertFalse(g.VERBOSE)
        
    @patch('edir_reminder_service_main.run')
    def test_050_debug_increase_g_debug(self, mock_run):
        rc = main(['-c', os.path.dirname(__file__) + "/password.conf", '-d', '--debug', '-d'])
        self.assertEqual(rc, 0)
        
        self.assertTrue(mock_run.called)
        self.assertEqual(g.DEBUG, 3)

    @patch('edir_reminder_service_main.run')
    def test_060_verbose_sets_g_verbose(self, mock_run):
        rc = main(['-c', os.path.dirname(__file__) + "/password.conf", '-v'])
        self.assertEqual(rc, 0)
        
        self.assertTrue(mock_run.called)
        self.assertTrue(g.VERBOSE)
        
    @patch('edir_reminder_service_main.run')
    def test_070_time_sets_now_timestamp(self, mock_run):
        rc = main(['-c', os.path.dirname(__file__) + "/password.conf", '--time', '20140825163831Z' ])
        self.assertEqual(rc, 0)
        
        self.assertTrue(mock_run.called)
        self.assertEqual(g.NOW.strftime(g.LDAP_TIME_FORMAT), '20140825163831Z')
        
    @patch('edir_reminder_service_main.run')
    def test_080_dry_sets_config_test_dry(self, mock_run):
        rc = main(['-c', os.path.dirname(__file__) + "/password.conf", '--dry' ])
        self.assertEqual(rc, 0)
        self.assertTrue(mock_run.called)
        
        config = mock_run.call_args[0][0]
        self.assertTrue(config.test.dry)

    @patch('edir_reminder_service_main.run')
    def test_090_test_sets_config_test_test(self, mock_run):
        rc = main(['-c', os.path.dirname(__file__) + "/password.conf", '--test', 'foo@localhost' ])
        self.assertEqual(rc, 0)
        self.assertTrue(mock_run.called)
        
        config = mock_run.call_args[0][0]
        self.assertTrue(config.test.test)
        self.assertEqual(config.test.to_address, 'foo@localhost')
        
    @patch('edir_reminder_service_main.run')
    def test_100_restrict_sets_config_test_restrict_to_users(self, mock_run):
        rc = main(['-c', os.path.dirname(__file__) + "/password.conf", '--restrict', ' foo1;foo2 ;cn=foo3,ou=users,dc=localhost;;;' ])
        self.assertEqual(rc, 0)
        self.assertTrue(mock_run.called)
        
        config = mock_run.call_args[0][0]
        self.assertEqual(config.test.restrict_to_users, set(['foo1', 'foo2', 'cn=foo3,ou=users,dc=localhost']))
        
    @patch('edir_reminder_service_main.run')
    def test_110_k_sets_config_ignore_cert(self, mock_run):
        rc = main(['-c', os.path.dirname(__file__) + "/password.conf", '-k' ])
        self.assertEqual(rc, 0)
        self.assertTrue(mock_run.called)
        
        config = mock_run.call_args[0][0]
        self.assertTrue(config.ignore_cert)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestMain)
    unittest.TextTestRunner(verbosity=2).run(suite)
