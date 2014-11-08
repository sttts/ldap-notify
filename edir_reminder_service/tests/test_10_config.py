import unittest
import os

import edir_reminder_service.config

class TestConfig(unittest.TestCase):
    def test_10_default_config_loads(self):
        c = edir_reminder_service.config.load()
        
        # some selection of default values
        self.assertEqual(c.server, 'ldap://localhost')
        self.assertEqual(c.bind_password, None)
        self.assertEqual(c.starttls, False)
        self.assertFalse(c.ignore_cert)
        self.assertEqual(c.smtp.ssl, False)
        self.assertEqual(c.smtp.starttls, False)
        self.assertEqual(c.smtp.password, None)
        self.assertTrue(c.admin.from_address.startswith('root@'))
        self.assertTrue(c.admin.to_address.startswith('admin@'))
        self.assertEqual(c.test.dry, False)
        self.assertEqual(c.test.test, False)
        self.assertTrue(c.test.to_address.startswith('root@'))
        self.assertEqual(c.test.restrict_to_users, set())
        self.assertEqual(c.rules, [])


    def test_20_loads_config(self):
        c = edir_reminder_service.config.load(os.path.dirname(__file__) + "/password.conf")
        
        self.assertEqual(c.server, 'ldap://localhost')
        self.assertEqual(c.base_context, 'dc=localhost')
        self.assertEqual(c.bind_dn, 'cn=admin,ou=users,dc=localhost')
        self.assertEqual(c.bind_password, 'admin_secret')
        self.assertEqual(c.starttls, True)
        self.assertEqual(c.expiry_attribute, 'passwordExpirationTime')
        self.assertEqual(c.notify_attribute, 'pwmNotify')
        self.assertEqual(c.smtp.server, 'localhost')
        self.assertEqual(len(c.rules), 5)
        self.assertEqual(c.rules[0].from_text, 'Login Reminder')
        self.assertEqual(c.rules[0].subject, 'Tomorrow')
        self.assertTrue(c.rules[0].from_address.startswith('root@'))
        self.assertTrue(c.rules[0].text_template.endswith("/templates/notify.tmpl.txt"))
        self.assertEqual(c.rules[1].subject, '$days_left days left')

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestConfig)
    unittest.TextTestRunner(verbosity=2).run(suite)