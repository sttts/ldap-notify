import unittest
import datetime
from datetime import timedelta
from mockldap import MockLdap

import ldap_notify.globals as g

def ldap_time(**kwargs):
    return (datetime.datetime.utcnow() + timedelta(**kwargs)).strftime(g.LDAP_TIME_FORMAT)

def ldap_user(name, mail=None, ou='ou=users,dc=localhost', pwmUser=True, expire=45, notify_string=None, grace=3, disabled=False, fullName=None):
    dn = 'cn=%s,%s' % (name, ou)
    pwd = '%s_secret' % name
    attr = {
        'cn': [name],
        'dn': [dn],
        'userPassword': [pwd],
        'passwordExpirationTime': [ldap_time(days=expire)],
        'loginGraceRemaining': [grace],
        'loginDisabled': ['true' if disabled else 'false'],
        'objectClass': ['top', 'person'] + ['pwmUser'] if pwmUser else [],
        'fullName': fullName if fullName else name
    }
    if mail is not None:
        attr['mail'] = [mail]
    if notify_string is not None:
        attr['pwmNotify'] = [notify_string]

    return (dn, attr)

class LocalLDAPTests(unittest.TestCase):
    # This is the content of our mock LDAP directory. It takes the form
    # {dn: {attr: [value, ...], ...}, ...}.
    directory = dict([
        ('dc=localhost', {'dc': ['localhost']}),
        ('ou=users,dc=localhost', {'ou': ['users']}),
        ('ou=admins,dc=localhost', {'ou': ['users']}),
        ldap_user('ceo', 'ceo@localhost'),
        ldap_user('cto', 'cto@localhost'),
        ldap_user('bob', 'bob@localhost'),
        ldap_user('http', pwmUser=False),
        ldap_user('alice', 'alice@localhost'),
        ldap_user('root', 'root@localhost', ou='ou=admins,dc=localhost')
    ])
    
    def addUser(self, name=None, mail=None, ou='ou=users,dc=localhost', expire=None, notified=None, disabled=False, grace=3):
        if not name:
            if expire < 0:
                name = "expired_%i_days_ago" % -expire
            else:
                name = "expires_in_%i_days" % expire
                
        if mail==True:
            mail = name + '@localhost'
            
        if notified:
            notified_days, rule = notified
            notify_string = '%s:%i' % (ldap_time(days=notified_days), rule)
        else:
            notify_string = None
      
        dn, attrs = ldap_user(name, mail=mail, ou=ou, expire=expire, notify_string=notify_string, grace=grace, disabled=disabled)
        print 'Adding user dn=%s: %r' % (dn, attrs)
        self.ldapobj.add_s(dn, attrs.items())
    
    @classmethod
    def setUpClass(cls):
        cls.mockldap = MockLdap(cls.directory)

    @classmethod
    def tearDownClass(cls):
        del cls.mockldap

    def setUp(self):
        # Patch ldap.initialize
        self.mockldap.start()
        self.ldapobj = self.mockldap['ldap://ldap']
        
    def tearDown(self):
        # Stop patching ldap.initialize and reset state.
        self.mockldap.stop()
        del self.ldapobj
