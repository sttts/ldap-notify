import ldap
from datetime import timedelta, datetime
import logging
log = logging.getLogger('edir-reminder-server')
					
import edir_reminder_service.globals as g

def search_users(config, con, fltr=""):
	attr_list = ["mail", "cn", "loginDisabled", config.notify_attribute, config.expiry_attribute]
	log.info("Searching for (&(objectclass=pwmUser)%s) at '%s' and its subtree" % (fltr, config.base_context))
	users = con.search_s(config.base_context, ldap.SCOPE_SUBTREE, "(&(objectclass=pwmUser)%s)" % fltr, attr_list)
	return users

def users_for_rule(config, con, rule):
	users = search_users(config, con, "(&(%s>=%s)(!(%s>=%s)))" % (config.expiry_attribute, rule.start, config.expiry_attribute, rule.end))	
	filtered_users = []
	skipped_users = []
	for cn, ldap_user in users:
		# filter out those whose notify attribute shows a notification in less of the days of this rule
		if config.notify_attribute in ldap_user:
			try:
				ts, last_rule = ldap_user[config.notify_attribute][0].split(':')
				ts = datetime.strptime(ts, g.LDAP_TIME_FORMAT)
				expiry = datetime.strptime(ldap_user[config.expiry_attribute][0])
				delta = expiry - ts
				if delta < timedelta(days=rule.days):
					log.info("Skipping %s because reminder %s was sent before: %s" % (cn, last_rule, ldap_user[config.notify_attribute]))
					skipped_users.append( (cn, ldap_user) )
					continue
			except ValueError, e:
				log.warn('Skipping %s because: %s' % (cn, str(e)))
				continue
			except Exception, e:
				log.exception(e)
				continue

		log.debug('Found %s with %s=%s to be notified with rule %i' % (cn, config.expiry_attribute, ldap_user[config.expiry_attribute][0], rule.days))
		filtered_users.append( (cn, ldap_user) )

	return filtered_users, skipped_users


def mark_user_notified(config, con, user, rule):
	cn, _ = user
	marker = g.NOW.strftime(g.LDAP_TIME_FORMAT) + ':' + str(rule.days)
	log.debug('Marking user %s notified with %s' % (cn, marker))
	if not g.DRY_RUN:
		con.modify_s(cn, [
			(ldap.MOD_REPLACE, config.notify_attribute, marker)
		])
