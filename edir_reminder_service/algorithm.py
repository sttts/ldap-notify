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

def users_for_rule(config, con, rule):
    users = search_users(config, con, "(&(%s>=%s)(!(%s>=%s)))" % (config.expiry_attribute, rule.start, config.expiry_attribute, rule.end))    
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
        
        # convert ldap user into Python user object
        json_user = {
            'cn': cn,
            'mail': None,
            config.notify_attribute: None,
            config.expiry_attribute: None,
            'fullName': None
        }
        for attr in ldap_user:
            if attr==config.notify_attribute:
                to_attr = 'notify'
            elif attr==config.expiry_attribute:
                to_attr = 'expiry'
            else:
                to_attr = attr
            json_user[to_attr] = ldap_user[attr][0]
        result.append(utils.obj(json_user))

    return result


def mark_user_notified(config, con, user, rule):
    marker = g.NOW.strftime(g.LDAP_TIME_FORMAT) + ':' + str(rule.days)
    log.info('%sMarking user %s notified with %s' % ('DRY: ' if config.test.dry else 'TEST:' if config.test.test else '', 
                                                    user.cn, marker))
    if not config.test.dry:
        con.modify_s(user.cn, [
            (ldap.MOD_REPLACE, config.notify_attribute, marker)
        ])
        

def process_rule_users(config, con, users, rule):
    users_without_email = filter(lambda u: not u.mail, users)
    users_with_email = filter(lambda u: u.mail, users)
    
    mailer = mail.MailHandler(config)
    for user in users_with_email:
        try:
            mailer.send_user_mail(rule, user)
            mark_user_notified(config, con, user, rule)
        except Exception:
            log.exception('Exception processing user %s' + user.cn)
