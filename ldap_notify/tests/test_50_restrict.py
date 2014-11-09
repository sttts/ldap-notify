import os
from mock import *
from StringIO import StringIO

from ldap_notify.tests.base import LocalLDAPTests, ldap_time
import ldap_notify.main
from ldap_notify.main import main

class TestRestrict(LocalLDAPTests):
    @patch('sys.stderr', new_callable=StringIO)
    @patch('ldap_notify.main.run', wraps=ldap_notify.main.run)
    @patch('smtplib.SMTP')
    def test_10_only_sends_to_restricted_users(self, mock_smtp, mock_run, mock_stderr):
        # prepare users
        for days in [-2, 0.5, 2, 5, 9, 20, 35]:
            self.addUser(expire=days, mail=True)
            
        self.addUser(expire=23, mail=True, name="mytestuser")
        
        # call tool
        rc = main(['-c', os.path.dirname(__file__) + "/password.conf", '--restrict', 'mytestuser'])
        self.assertEqual(mock_stderr.getvalue(), '')
        self.assertEqual(rc, 0)

        # only admin report and mail to the mytestuser
        SMTP = mock_smtp.return_value
        (config,), _ = mock_run.call_args
        self.assertEqual(SMTP.sendmail.call_count, 2)
        self.assertEqual(map(lambda x: x[1][1], SMTP.sendmail.mock_calls), ['mytestuser@localhost', config.admin.to_address])

    @patch('sys.stderr', new_callable=StringIO)
    @patch('ldap_notify.main.run', wraps=ldap_notify.main.run)
    @patch('smtplib.SMTP')
    def test_10_only_sends_to_restricted_users_with_dn(self, mock_smtp, mock_run, mock_stderr):
        # prepare users
        for days in [-2, 0.5, 2, 5, 9, 20, 35]:
            self.addUser(expire=days, mail=True)
            
        self.addUser(expire=23, mail=True, name="mytestuser")
        
        # call tool
        rc = main(['-c', os.path.dirname(__file__) + "/password.conf", '--restrict', 'cn=mytestuser,ou=users,dc=localhost'])
        self.assertEqual(mock_stderr.getvalue(), '')
        self.assertEqual(rc, 0)

        # only admin report and mail to the mytestuser
        SMTP = mock_smtp.return_value
        self.assertEqual(SMTP.sendmail.call_count, 2)

if __name__ == '__main__':
    import nose
    nose.run(defaultTest=__name__)
