import ldap
from datetime import timedelta, datetime
import logging
log = logging.getLogger('ldap_notify.algorithm')
                    
import ldap_notify.globals as g
import ldap_notify.utils as utils
import ldap_notify.mail as mail

def search_users(config, con, fltr=""):
    attr_list = ["mail", "cn", config.notify_attribute, config.expiry_attribute, 'fullName', 'loginGraceRemaining']
    fltr = "(&(objectClass=%s)(!(loginDisabled=true))%s)" % (config.user_objectclass, fltr)
    users = []
    for dn in (config.base_dn or ['']):
        log.info("Searching for %s at '%s'%s" % (fltr, dn, ' and its subtree' if config.subtree_search else ''))
        dn_users = con.search_s(dn, ldap.SCOPE_SUBTREE if config.subtree_search else ldap.SCOPE_ONELEVEL, fltr, attr_list)
        users.extend(dn_users)
    return users

def ldap_user_to_user(config, cn, ldap_user):
    json_user = {
        'dn': cn,
        'cn': None,
        'mail': None,
        config.notify_attribute: None,
        config.expiry_attribute: None,
        'fullName': None,
        'rule': None
    }
    for attr in ldap_user:
        if attr==config.notify_attribute:
            to_attr = 'notify'
        elif attr==config.expiry_attribute:
            to_attr = 'expiry'
        else:
            to_attr = attr
        json_user[to_attr] = ldap_user[attr][0]
    return utils.obj(json_user)
    

def search_users_without_grace_logins(config, con):
    users = search_users(config, con, "(loginGraceRemaining=0)")    
    return list(ldap_user_to_user(config, cn, ldap_user) for cn, ldap_user in users)


def users_for_rule(config, con, rule):
    users = search_users(config, con, "(&(%s>=%s)(!(%s>=%s))(!(loginGraceRemaining=0)))" % (config.expiry_attribute, rule.start, config.expiry_attribute, rule.end))    
    result = []
    for dn, ldap_user in users:
        # filter out those whose notify attribute shows a notification in less of the days of this rule
        if config.notify_attribute in ldap_user:
            try:
                # check old notify attribute
                if config.notify_attribute in ldap_user:
                    notify_attribute_value = ldap_user[config.notify_attribute][0]
                    parts = notify_attribute_value.split(':')                    
                        
                    def fix_user():
                        log.warn("%sDeleting invalid attribute of %s: '%s: %s'" % ('DRY: ' if config.dry else 'TEST:' if config.test.enabled else '',
                                                                                 dn, config.notify_attribute, notify_attribute_value))
                        if not config.dry and not config.test.enabled:
                            con.modify_s(dn, [
                                (ldap.MOD_DELETE, config.notify_attribute, notify_attribute_value)
                            ])

                    if len(parts) != 2:
                        fix_user()
                    else:
                        # try notify attribute type conversion
                        try:
                            last_rule = int(parts[1])
                            last_notify = datetime.strptime(parts[0], g.LDAP_TIME_FORMAT)
                            expiry = datetime.strptime(ldap_user[config.expiry_attribute][0], g.LDAP_TIME_FORMAT)
                        except TypeError:
                            fix_user()
                        else:                                
                            # skip users without email: their notification is only sent once to the admins.
                            # At this point this happened already.
                            if 'mail' not in ldap_user:
                                log.debug("Skipping %s because reminder %s was sent to admins before: %s" % (dn, last_rule, ldap_user[config.notify_attribute]))
                                continue
                                                    
                            if not (expiry - last_notify >= timedelta(days=last_rule) or last_rule > rule.days):
                                if g.DEBUG > 1:
                                    log.debug("Skipping %s because reminder %s was sent before: %s" % (dn, last_rule, ldap_user[config.notify_attribute]))
                                continue
                    
                # users without email will notify the admin later
                if 'mail' not in ldap_user:
                    log.info("User %s has no email" % dn)
            except ValueError, e:
                log.exception('Skipping %s because: %s' % (dn, str(e)))
                continue
            except Exception, e:
                log.exception(e)
                continue

        log.debug('Found %s with %s=%s to be notified with rule %i' % (dn, config.expiry_attribute, ldap_user[config.expiry_attribute][0], rule.days))
        result.append(ldap_user_to_user(config, dn, ldap_user))

    return result


def mark_user_notified(config, con, user, rule, restricted):
    marker = g.NOW.strftime(g.LDAP_TIME_FORMAT) + ':' + str(rule.days)
    log.info('%sMarking user %s notified with %s' % ('RESTRICTED: ' if restricted else 'DRY: ' if config.dry else '', 
                                                    user.cn, marker))
    if not restricted and not config.dry and not config.test.enabled:
        con.modify_s(user.dn, [
            (ldap.MOD_REPLACE, config.notify_attribute, marker)
        ])
    

def notify_users(config, con, users, rule):
    mailer = mail.MailHandler(config)
    failed = []
    notified = []
    for user in users:
        try:
            restricted = config.restrict_to_users and not (user.cn in config.restrict_to_users or user.dn in config.restrict_to_users)
            mailer.send_user_mail(rule, user, restricted)
            mark_user_notified(config, con, user, rule, restricted)
            notified.append(user)
        except Exception:
            log.exception('Exception processing user %s' + user.cn)
            failed.append(user)
    return notified, failed


def user_to_rule_line(user, rule):
    return "%s, %s%sExpiry Date: %s" % (
        user.dn, 
        (user.mail+', ') if user.mail else '', 
        ("%i Days Rule, " % user.rule.days) if user.rule else '',
        str(datetime.strptime(user.expiry, '%Y%m%d%H%M%SZ')))


def notify_admin(config, con, notified_users, failed_users, users_without_email, users_without_grace_logins):
    mailer = mail.MailHandler(config)
    
    notified_lines = list(user_to_rule_line(user, user.rule) for user in notified_users)
    failed_lines = list(user_to_rule_line(user, user.rule) for user in failed_users)
    without_email_lines = list(user_to_rule_line(user, user.rule) for user in users_without_email)
    no_grace_logins_lines = list(user_to_rule_line(user, user.rule) for user in users_without_grace_logins)
    
    mailer.send_admin_report(config, notified_lines, failed_lines, without_email_lines, no_grace_logins_lines)
            

    
