import ldap
from datetime import timedelta, datetime
import logging
log = logging.getLogger('edir_reminder_service.algorithm')
                    
import edir_reminder_service.globals as g
import edir_reminder_service.utils as utils
import edir_reminder_service.mail as mail

def search_users(config, con, fltr=""):
    attr_list = ["mail", "cn", "loginDisabled", config.notify_attribute, config.expiry_attribute, 'fullName']
    log.info("Searching for (&(objectclass=pwmUser)%s) at '%s' and its subtree" % (fltr, config.base_context))
    users = con.search_s(config.base_context, ldap.SCOPE_SUBTREE, "(&(objectclass=pwmUser)%s)" % fltr, attr_list)
    return users

def ldap_user_to_user(config, cn, ldap_user):
    json_user = {
        'cn': cn,
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
    users = search_users(config, con, "(&(loginGraceRemaining=0)(loginDisabled=false))")    
    return list(ldap_user_to_user(config, cn, ldap_user) for cn, ldap_user in users)


def users_for_rule(config, con, rule):
    users = search_users(config, con, "(&(%s>=%s)(!(%s>=%s))(!(loginGraceRemaining=0)))" % (config.expiry_attribute, rule.start, config.expiry_attribute, rule.end))    
    result = []
    for cn, ldap_user in users:
        # filter out those whose notify attribute shows a notification in less of the days of this rule
        if config.notify_attribute in ldap_user:
            try:
                # disabled users are skipped
                if 'loginDisabled' in ldap_user and ldap_user['loginDisabled'][0]:
                    log.debug("Skipping %s because it's disabled" % cn)
                    continue

                # check old notify attribute
                if config.notify_attribute in ldap_user:
                    notify_attribute_value = ldap_user[config.notify_attribute][0]
                    parts = notify_attribute_value.split(':')                    
                        
                    def fix_user():
                        log.warn("%sDeleting invalid attribute of %s: '%s: %s'" % ('DRY: ' if config.test.dry else 'TEST:' if config.test.test else '',
                                                                                 cn, config.notify_attribute, notify_attribute_value))
                        if not config.test.dry:
                            con.modify_s(cn, [
                                (ldap.MOD_DELETE, config.notify_attribute)
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
                                log.debug("Skipping %s because reminder %s was sent to admins before: %s" % (cn, last_rule, ldap_user[config.notify_attribute]))
                                continue
                                                    
                            if expiry - last_notify < timedelta(days=last_rule) and last_rule <= rule.days:
                                if g.DEBUG > 1:
                                    log.debug("Skipping %s because reminder %s was sent before: %s" % (cn, last_rule, ldap_user[config.notify_attribute]))
                                continue
                    
                # users without email will notify the admin later
                if 'mail' not in ldap_user:
                    log.info("User %s has no email" % cn)
            except ValueError, e:
                log.exception('Skipping %s because: %s' % (cn, str(e)))
                continue
            except Exception, e:
                log.exception(e)
                continue

        log.debug('Found %s with %s=%s to be notified with rule %i' % (cn, config.expiry_attribute, ldap_user[config.expiry_attribute][0], rule.days))
        result.append(ldap_user_to_user(config, cn, ldap_user))

    return result


def mark_user_notified(config, con, user, rule):
    marker = g.NOW.strftime(g.LDAP_TIME_FORMAT) + ':' + str(rule.days)
    log.info('%sMarking user %s notified with %s' % ('DRY: ' if config.test.dry else 'TEST:' if config.test.test else '', 
                                                    user.cn, marker))
    if not config.test.dry:
        con.modify_s(user.cn, [
            (ldap.MOD_REPLACE, config.notify_attribute, marker)
        ])
    

def notify_users(config, con, users, rule):
    mailer = mail.MailHandler(config)
    failed = []
    notified = []
    for user in users:
        try:
            mailer.send_user_mail(rule, user)
            mark_user_notified(config, con, user, rule)
            notified.append(user)
        except Exception:
            log.exception('Exception processing user %s' + user.cn)
            failed.append(user)
    return notified, failed


def user_to_rule_line(user, rule):
    return "cn=%s, %s%sExpiry Date: %s" % (
        user.cn, 
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
            

    