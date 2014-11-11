import os
from mock import *
from StringIO import StringIO

from ldap_notify.tests.base import LocalLDAPTests, ldap_time
import ldap_notify.main
from ldap_notify.main import main

class TestAlgorithm(LocalLDAPTests):
    @patch('sys.stderr', new_callable=StringIO)
    @patch('ldap_notify.main.run', wraps=ldap_notify.main.run)
    @patch('smtplib.SMTP')
    def test_10_finds_expired_users(self, mock_smtp, mock_run, mock_stderr):
        # prepare users
        for days in [-2, 0.5, 2, 5, 9, 20, 35]:
            self.addUser(expire=days, mail=True)
        
        # call tool
        rc = main(['-c', os.path.dirname(__file__) + "/password.conf"])
        self.assertEqual(mock_stderr.getvalue(), '')
        self.assertEqual(rc, 0)

        # mails to all but -2 and 35 + admin report
        SMTP = mock_smtp.return_value
        self.assertEqual(SMTP.sendmail.call_count, 6)

    @patch('sys.stderr', new_callable=StringIO)
    @patch('ldap_notify.main.run', wraps=ldap_notify.main.run)
    @patch('smtplib.SMTP')
    def test_15_finds_expired_users_in_all_base_contexts(self, mock_smtp, mock_run, mock_stderr):
        self.addUser(name='lazyadmin', expire=12, mail=True, ou='ou=admins,dc=localhost')

        rc = main(['-c', os.path.dirname(__file__) + "/password.conf"])
        self.assertEqual(mock_stderr.getvalue(), '')
        self.assertEqual(rc, 0)

        SMTP = mock_smtp.return_value
        self.assertEqual(SMTP.sendmail.call_count, 2)

    @patch('sys.stderr', new_callable=StringIO)
    @patch('ldap_notify.main.run', wraps=ldap_notify.main.run)
    @patch('smtplib.SMTP')
    def test_20_sends_notification_only_once(self, mock_smtp, mock_run, mock_stderr):
        # prepare users
        for days in [-2, 0.5, 2, 5, 9, 20, 35]:
            self.addUser(expire=days, mail=True)
        
        # call tool one time
        rc = main(['-c', os.path.dirname(__file__) + "/password.conf"])
        self.assertEqual(mock_stderr.getvalue(), '')
        self.assertEqual(rc, 0)

        # 7 mails as before
        SMTP = mock_smtp.return_value
        self.assertEqual(SMTP.sendmail.call_count, 6)

        # call tool a second time
        rc = main(['-c', os.path.dirname(__file__) + "/password.conf"])
        self.assertEqual(mock_stderr.getvalue(), '')
        self.assertEqual(rc, 0)

        # only the admin report, the other user were notified before
        self.assertEqual(SMTP.sendmail.call_count, 7)

    @patch('sys.stderr', new_callable=StringIO)
    @patch('ldap_notify.main.run', wraps=ldap_notify.main.run)
    @patch('smtplib.SMTP')
    def test_30_notify_again_when_time_passes(self, mock_smtp, mock_run, mock_stderr):
        # prepare users
        for days in [-2, 0.5, 2, 5, 9, 20, 35]:
            self.addUser(expire=days, mail=True)
        
        # call tool one time
        rc = main(['-c', os.path.dirname(__file__) + "/password.conf"])
        self.assertEqual(mock_stderr.getvalue(), '')
        self.assertEqual(rc, 0)
        SMTP = mock_smtp.return_value
        self.assertEqual(SMTP.sendmail.call_count, 6)

        # call tool a second time, second server an hour later
        rc = main(['-c', os.path.dirname(__file__) + "/password.conf", '--time', ldap_time(hours=1)])
        self.assertEqual(mock_stderr.getvalue(), '')
        self.assertEqual(rc, 0)
        self.assertEqual(SMTP.sendmail.call_count, 7)

        # a day and a bit later:
        # - user 2 => rule 1 appies now
        rc = main(['-c', os.path.dirname(__file__) + "/password.conf", '--time', ldap_time(days=1, hours=1)])
        self.assertEqual(mock_stderr.getvalue(), '')
        self.assertEqual(rc, 0)
        self.assertEqual(SMTP.sendmail.call_count, 9)

        # 2 days and a bit later:
        # - user 5 => rule 3 appies now
        # - user 9 => rule 7 applies now
        rc = main(['-c', os.path.dirname(__file__) + "/password.conf", '--time', ldap_time(days=2, hours=1)])
        self.assertEqual(mock_stderr.getvalue(), '')
        self.assertEqual(rc, 0)
        self.assertEqual(SMTP.sendmail.call_count, 12)

        # 6 days and a bit later:
        # - user 9 => rule 3 appies now
        # - user 20 => rule 14 applies now
        # - user 35 => rule 30 applies now
        rc = main(['-c', os.path.dirname(__file__) + "/password.conf", '--time', ldap_time(days=6, hours=1)])
        self.assertEqual(mock_stderr.getvalue(), '')
        self.assertEqual(rc, 0)
        self.assertEqual(SMTP.sendmail.call_count, 16)

    @patch('sys.stderr', new_callable=StringIO)
    @patch('ldap_notify.main.run', wraps=ldap_notify.main.run)
    @patch('smtplib.SMTP')
    def test_40_notifies_again_after_smtp_error(self, mock_smtp, mock_run, mock_stderr):
        self.addUser(expire=23, mail=True)

        # refuse SMTP connection
        import smtplib
        mock_smtp.side_effect = smtplib.SMTPConnectError(42, 'Connection refused')

        # call tool one time
        rc = main(['-c', os.path.dirname(__file__) + "/password.conf"])
        self.assertEqual(mock_stderr.getvalue(), "SMTP error: (42, 'Connection refused')\n")
        self.assertEqual(rc, 1)
        SMTP = mock_smtp.return_value
        self.assertEqual(SMTP.sendmail.call_count, 0)
        
        # 7 days and a bit later without SMTP problems
        mock_smtp.side_effect = None
        rc = main(['-c', os.path.dirname(__file__) + "/password.conf", '--time', ldap_time(hours=1)])
        self.assertEqual(rc, 0)
        self.assertEqual(SMTP.sendmail.call_count, 2)
        
    @patch('sys.stderr', new_callable=StringIO)
    @patch('ldap_notify.main.run', wraps=ldap_notify.main.run)
    @patch('smtplib.SMTP')
    def test_50_notify_again_with_old_notify_values(self, mock_smtp, mock_run, mock_stderr):
        self.addUser(expire=35, mail=True, notified=(-178,7))

        # call tool one time
        rc = main(['-c', os.path.dirname(__file__) + "/password.conf"])
        self.assertEqual(mock_stderr.getvalue(), '')
        self.assertEqual(rc, 0)
        SMTP = mock_smtp.return_value
        self.assertEqual(SMTP.sendmail.call_count, 1)
        
        # 7 days and a bit later
        rc = main(['-c', os.path.dirname(__file__) + "/password.conf", '--time', ldap_time(days=7, hours=1)])
        self.assertEqual(mock_stderr.getvalue(), '')
        self.assertEqual(rc, 0)
        self.assertEqual(SMTP.sendmail.call_count, 3)
        
    @patch('sys.stderr', new_callable=StringIO)
    @patch('ldap_notify.main.run', wraps=ldap_notify.main.run)
    @patch('smtplib.SMTP')
    def test_60_does_not_sends_users_mails_in_dry_mode(self, mock_smtp, mock_run, mock_stderr):
        # prepare users
        for days in [-2, 0.5, 2, 5, 9, 20, 35]:
            self.addUser(expire=days, mail=True)

        # call tool one time
        rc = main(['-c', os.path.dirname(__file__) + "/password.conf", '--dry'])
        self.assertEqual(mock_stderr.getvalue(), '')
        self.assertEqual(rc, 0)
        SMTP = mock_smtp.return_value
        self.assertEqual(SMTP.sendmail.call_count, 0)

    @patch('sys.stderr', new_callable=StringIO)
    @patch('ldap_notify.main.run', wraps=ldap_notify.main.run)
    @patch('smtplib.SMTP')
    def test_60_ignores_disabled_users(self, mock_smtp, mock_run, mock_stderr):
        # prepare users
        for days in [-2, 0.5, 2, 5, 9, 20, 35]:
            self.addUser(expire=days, mail=True)
            
        self.addUser(expire=23, mail=True, disabled=True)

        # call tool one time
        rc = main(['-c', os.path.dirname(__file__) + "/password.conf"])
        self.assertEqual(mock_stderr.getvalue(), '')
        self.assertEqual(rc, 0)
        SMTP = mock_smtp.return_value
        self.assertEqual(SMTP.sendmail.call_count, 6)
        
    @patch('sys.stderr', new_callable=StringIO)
    @patch('ldap_notify.main.run', wraps=ldap_notify.main.run)
    @patch('smtplib.SMTP')
    def test_70_does_not_send_mails_for_users_without_mail(self, mock_smtp, mock_run, mock_stderr):
        # prepare users
        for days in [-2, 0.5, 2, 5, 9, 20, 35]:
            self.addUser(expire=days, mail=True if days!=9 else False)
            
        self.addUser(expire=23, mail=False)

        # call tool one time
        rc = main(['-c', os.path.dirname(__file__) + "/password.conf"])
        self.assertEqual(mock_stderr.getvalue(), '')
        self.assertEqual(rc, 0)
        SMTP = mock_smtp.return_value
        self.assertEqual(SMTP.sendmail.call_count, 5)

if __name__ == '__main__':
    import nose
    nose.run(defaultTest=__name__)
