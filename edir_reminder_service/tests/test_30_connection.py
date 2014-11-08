import unittest
import os
from mock import *
from StringIO import StringIO

from edir_reminder_service.tests.base import LocalLDAPTests
import edir_reminder_service_main
from edir_reminder_service_main import main

class TestConnection(LocalLDAPTests):
    @patch('sys.stderr', new_callable=StringIO)
    @patch('smtplib.SMTP')
    def test_10_connect_with_tls_and_bind(self, mock_smtp, mock_stderr):
        rc = main(['-c', os.path.dirname(__file__) + "/password-tls.conf"])
        self.assertEqual(mock_stderr.getvalue(), '')
        self.assertEqual(rc, 0)

        self.assertTrue(self.ldapobj.methods_called() >= ['initialize', 'start_tls_s', 'simple_bind_s', 'search_s'], self.ldapobj.methods_called())
        #self.assertTrue(mock_smtplib_STMP)
        
    @patch('sys.stderr', new_callable=StringIO)
    @patch("smtplib.SMTP")
    def test_20_connect_without_tls(self, mock_smtp, mock_stderr):
        rc = main(['-c', os.path.dirname(__file__) + "/password.conf"])
        self.assertEqual(mock_stderr.getvalue(), '')
        self.assertEqual(rc, 0)

        self.assertTrue(self.ldapobj.methods_called() >= ['initialize', 'simple_bind_s', 'search_s'], self.ldapobj.methods_called())
     
    @patch('sys.stderr', new_callable=StringIO)
    @patch('edir_reminder_service_main.run', wraps=edir_reminder_service_main.run)
    @patch('smtplib.SMTP')
    def test_30_sends_admin_report(self, mock_smtp, mock_run, mock_stderr):
        rc = main(['-c', os.path.dirname(__file__) + "/password.conf"])
        self.assertEqual(mock_stderr.getvalue(), '')
        self.assertEqual(rc, 0)

        SMTP = mock_smtp.return_value
        self.assertEqual(SMTP.sendmail.call_count, 1)

        (config,), _ = mock_run.call_args
        sendmail_args, _ = SMTP.sendmail.call_args
        self.assertEqual(sendmail_args[:2], (config.admin.from_address, config.admin.to_address))

    @patch('sys.stderr', new_callable=StringIO)
    @patch('edir_reminder_service_main.run', wraps=edir_reminder_service_main.run)
    @patch('smtplib.SMTP')
    def test_40_sends_no_admin_mail_in_dry_mode(self, mock_smtp, mock_run, mock_stderr):
        rc = main(['-c', os.path.dirname(__file__) + "/password.conf", '--dry'])
        self.assertEqual(mock_stderr.getvalue(), '')
        self.assertEqual(rc, 0)

        SMTP = mock_smtp.return_value
        self.assertFalse(SMTP.sendmail.called)
        
    @patch('sys.stderr', new_callable=StringIO)
    @patch('edir_reminder_service_main.run', wraps=edir_reminder_service_main.run)
    @patch('smtplib.SMTP')
    def test_50_sends_admin_report_in_test_mode(self, mock_smtp, mock_run, mock_stderr):
        # prepare users
        for days in [-2, 0.5, 2, 5, 9, 20, 35]:
            self.addUser(expire=days, mail=True)
            
        rc = main(['-c', os.path.dirname(__file__) + "/password.conf", '--test', 'tester@localhost'])
        self.assertEqual(mock_stderr.getvalue(), '')
        self.assertEqual(rc, 0)

        # only mails to tester@localhost
        SMTP = mock_smtp.return_value
        self.assertEqual(SMTP.sendmail.call_count, 6)
        self.assertEqual(set(map(lambda x: x[1][1], SMTP.sendmail.mock_calls)), set(['tester@localhost']))

if __name__ == '__main__':
    import nose
    nose.run(defaultTest=__name__)