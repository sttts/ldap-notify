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
				# disabled users are skipped
				if 'loginDisabled' in ldap_user and ldap_user['loginDisabled'][0]:
					log.debug("Skipping %s because it's disabled" % cn)
					skipped_users.append( (cn, ldap_user) )
					continue

				# check old notify attribute
				if config.notify_attribute in ldap_user:
					notify_attribute_value = ldap_user[config.notify_attribute][0]
					parts = notify_attribute_value.split(':')
					if len(parts) != 2:
						log.warn("%sDeleting invalid attribute of %s: '%s: %s'" % ('DRY: ' if g.DRY_RUN else '', cn, config.notify_attribute, notify_attribute_value))
						if not g.DRY_RUN:
							con.modify_s(cn, [
								(ldap.MOD_DELETE, config.notify_attribute)
							])
					else:
						ts, last_rule = parts 
						ts = datetime.strptime(ts, g.LDAP_TIME_FORMAT)
						expiry = datetime.strptime(ldap_user[config.expiry_attribute][0], g.LDAP_TIME_FORMAT)
						delta = expiry - ts
						if delta < timedelta(days=rule.days):
							log.debug("Skipping %s because reminder %s was sent before: %s" % (cn, last_rule, ldap_user[config.notify_attribute]))
							skipped_users.append( (cn, ldap_user) )
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
		filtered_users.append( (cn, ldap_user) )

	return filtered_users, skipped_users


def mark_user_notified(config, con, user, rule):
	cn, _ = user
	marker = g.NOW.strftime(g.LDAP_TIME_FORMAT) + ':' + str(rule.days)
	log.info('%sMarking user %s notified with %s' % ('DRY: ' if g.DRY_RUN else '', cn, marker))
	if not g.DRY_RUN:
		con.modify_s(cn, [
			(ldap.MOD_REPLACE, config.notify_attribute, marker)
		])
