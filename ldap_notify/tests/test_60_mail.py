import os
import re
from mock import *
from StringIO import StringIO

from ldap_notify.tests.base import LocalLDAPTests, ldap_time
import ldap_notify.main
from ldap_notify.main import main

def grep(regex, l):
    return list(x for x in l if regex.search(x))

class TestMail(LocalLDAPTests):
    
    def assertIn(self, value, lst, msg=None):
        self.assertTrue(value in lst, msg or ('Search for: %s\n\n"""' % value + "\n".join(lst) + '"""'))
        
    def assertGrep(self, regex, lst, msg=None):
        self.assertTrue(grep(re.compile(regex), lst), msg or ('Regex search for: r"%s"\n\n"""' % regex + "\n".join(lst) + '"""'))
    
    @patch('sys.stderr', new_callable=StringIO)
    @patch('ldap_notify.main.run', wraps=ldap_notify.main.run)
    @patch('smtplib.SMTP')
    def test_10_sends_correct_user_emails(self, mock_smtp, mock_run, mock_stderr):
        self.addUser(name='expired_3', fullName="Alice", expire=3, mail=True)
        self.addUser(name='expired_23', expire=23, mail=True)
        self.addUser(name='no_mail', expire=3, mail=None)
        self.addUser(name='not_expired', expire=43, mail=True)
        self.addUser(name='no_grace', expire=3, mail=True, grace=0)
        self.addUser(name='disabled', expire=3, mail=True, disabled=True)
        
        # call tool
        rc = main(['-c', os.path.dirname(__file__) + "/password.conf"])
        self.assertEqual(mock_stderr.getvalue(), '')
        self.assertEqual(rc, 0)

        # emails to the right addresses?
        SMTP = mock_smtp.return_value
        (config,), _ = mock_run.call_args
        self.assertEqual(SMTP.sendmail.call_count, 3)
        user_mails = ['expired_3@localhost', 'expired_23@localhost']
        user_fullNames = ['Alice', 'expired_23']
        user_days = [3, 23]
        user_rule = [2, 4]
        self.assertEqual(map(lambda x: x[1][1], SMTP.sendmail.mock_calls)[:2], user_mails)
        
        for i in range(2):
            args = SMTP.sendmail.mock_calls[i][1]
            self.assertEqual(args[0], config.admin.from_address)
            self.assertEqual(args[1], user_mails[i])
            
            lines = args[2].split('\n')
            self.assertIn('Content-Type: text/plain; charset="utf-8"', lines)
            self.assertGrep(r"^From: %s <%s>$" % (config.rules[user_rule[i]].from_text.replace('$Object', '.*'), config.admin.from_address), lines)
            self.assertIn('To: %s' % user_mails[i], lines)
            self.assertIn('Dear %s,' % user_fullNames[i], lines)
            self.assertGrep(r'within %i days' % user_days[i], lines)

    @patch('sys.stderr', new_callable=StringIO)
    @patch('ldap_notify.main.run', wraps=ldap_notify.main.run)
    @patch('smtplib.SMTP')
    def test_15_sends_correct_html_user_emails(self, mock_smtp, mock_run, mock_stderr):
        self.addUser(name='expired_3', fullName="Alice", expire=3, mail=True)
        self.addUser(name='expired_12', expire=12, mail=True) # rule 14 has a html template
        self.addUser(name='no_mail', expire=3, mail=None)
        self.addUser(name='not_expired', expire=43, mail=True)
        self.addUser(name='no_grace', expire=3, mail=True, grace=0)
        self.addUser(name='disabled', expire=3, mail=True, disabled=True)
            
        # call tool
        rc = main(['-c', os.path.dirname(__file__) + "/password.conf"])
        self.assertEqual(mock_stderr.getvalue(), '')
        self.assertEqual(rc, 0)

        # emails to the right addresses?
        SMTP = mock_smtp.return_value
        (config,), _ = mock_run.call_args
        self.assertEqual(SMTP.sendmail.call_count, 3)
        
        # check only expiry_12 user
        args = SMTP.sendmail.mock_calls[1][1]
        self.assertEqual(args[0], config.admin.from_address)
        self.assertEqual(args[1], 'expired_12@localhost')
            
        lines = args[2].split('\n')
        self.assertIn('Content-Type: text/html; charset="utf-8"', lines)
        self.assertGrep(r"^From: %s <%s>$" % (config.rules[3].from_text.replace('$Object', '.*'), config.admin.from_address), lines)
        self.assertIn('To: %s' % 'expired_12@localhost', lines)

        # we also have a text mime part
        self.assertIn('Content-Type: text/plain; charset="utf-8"', lines)

    @patch('sys.stderr', new_callable=StringIO)
    @patch('ldap_notify.main.run', wraps=ldap_notify.main.run)
    @patch('smtplib.SMTP')
    def test_10_sends_correct_admin_email(self, mock_smtp, mock_run, mock_stderr):
        self.addUser(name='expired_3', expire=3, mail=True)
        self.addUser(name='expired_23', expire=3, mail=True)
        self.addUser(name='no_mail', expire=3, mail=None)
        self.addUser(name='not_expired', expire=43, mail=True)
        self.addUser(name='no_grace', expire=3, mail=True, grace=0)
        self.addUser(name='disabled', expire=3, mail=True, disabled=True)
        
        # call tool
        rc = main(['-c', os.path.dirname(__file__) + "/password.conf"])
        self.assertEqual(mock_stderr.getvalue(), '')
        self.assertEqual(rc, 0)

        # emails to the right addresses?
        SMTP = mock_smtp.return_value
        (config,), _ = mock_run.call_args
        self.assertEqual(SMTP.sendmail.call_count, 3)
        self.assertEqual(map(lambda x: x[1][1], SMTP.sendmail.mock_calls), ['expired_3@localhost', 'expired_23@localhost', config.admin.to_address])
        
        # admin email content correct?
        args = SMTP.sendmail.mock_calls[-1][1]
        self.assertEqual(args[0], config.admin.from_address)
        self.assertEqual(args[1], config.admin.to_address)
        
        lines = args[2].split('\n')
        self.assertIn('Content-Type: text/plain; charset="utf-8"', lines)
        self.assertGrep(r"^Subject: %s$" % (config.admin.subject.replace('$Object', '.*')), lines)
        self.assertGrep(r"^From: %s <%s>$" % (config.admin.from_text.replace('$Object', '.*'), config.admin.from_address), lines)
        self.assertIn('To: %s' % config.admin.to_address, lines)
        self.assertGrep(r"Without grace logins: *1$", lines)
        self.assertGrep(r"^Without email: *1$", lines)
        self.assertGrep(r'^Failed: *0$', lines)
        self.assertGrep(r'^Notified: *2$', lines)

if __name__ == '__main__':
    import nose
    nose.run(defaultTest=__name__)
