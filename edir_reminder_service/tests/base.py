import unittest
import datetime
from datetime import timedelta, datetime
import edir_reminder_service.globals as g


class FakeLDAPTests(unittest.TestCase):
    def setUp(self):
        from dataflake.fakeldap import TREE
        self.db = TREE
        self.db.addTreeItems('ou=users,dc=localhost')
        self.db.addTreeItems('ou=groups,dc=localhost')

    def tearDown(self):
        self.db.clear()

    def _getTargetClass(self):
        from dataflake.fakeldap import FakeLDAPConnection
        return FakeLDAPConnection

    def _makeOne(self, *args, **kw):
        conn = self._getTargetClass()(*args, **kw)
        return conn

    def addUser(self, name, mail=None, expiry=datetime.utcnow() + timedelta(days=47), notify=None):
        from dataflake.fakeldap.utils import hash_pwd
        conn = self._makeOne()
        user_dn = 'cn=%s,ou=users,dc=localhost' % name
        user_pwd = '%s_secret' % name

        if conn.hash_password:
            pwd = hash_pwd(user_pwd)
        else:
            pwd = user_pwd

        user = [ ('cn', [name])
               , ('userPassword', [pwd])
               , ('passwordExpirationTime'), [expiry.strftime(g.LDAP_TIME_FORMAT)]
               , ('loginGraceRemaining'), [3]
               , ('loginDisabled'), [False]
               , ('objectClass', ['top', 'person', 'pwnUser'])
               ]
        if mail is not None:
            user.append(('mail', [mail]))
        if notify is not None:
            user.append(('pwmNotify', [notify]))

        conn.add_s(user_dn, user)
        return (user_dn, user_pwd)

    def addGroup(self, name, members=None):
        conn = self._makeOne()
        group_dn = 'cn=%s,ou=groups,dc=localhost' % name

        group = [ ('cn', [name])
                , ('objectClass', ['top', 'group'])
                ]
        if members is not None:
            members = ['cn=%s,ou=users,dc=localhost' % x for x in members]
            group.append((conn.member_attr, members))

        conn.add_s(group_dn, group)
        return group_dn