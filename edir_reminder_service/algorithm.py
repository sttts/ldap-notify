import ldap
import logging
log = logging.getLogger('edir-reminder-server')
					
def users(config, con, fltr=""):
	attr_list = ["mail", "cn", config.notify_attribute, config.expiry_attribute]
	log.info("Searching for %s at '%s' and its subtree" % (fltr, config.base_context))
	users = con.search_s(config.base_context, ldap.SCOPE_SUBTREE, "(&(objectclass=User)%s)" % fltr, attr_list)
	return users

def users_for_rule(config, con, rule):
	return users(config, con, "(&(%s>=%s)(!(%s>=%s)))" % (config.expiry_attribute, rule.start, config.expiry_attribute, rule.end))

# 	ldap_filter = self._mkfilter(rule)
# 	search_attr = rule.search_attr
# 	for base in self.base:
# 		for u in self._search(base, ldap_filter, search_attr):
# 			try:
# 				user = {'dn': u[0], 'cn': u[1]['cn'][0],
# 						'mail': u[1]['mail'][0],
# 						'expires': u[1][search_attr][0]}
# 				self.log.debug('Found User ' + u[0] + 
# 							   ' with expiration date ' + 
# 							   user['expires'])
# 				user['notification_rule'] = rule.name
# 				user['notification_id'] = user['expires'] + ':' + user['notification_rule']
# 				user['notifications'] = u[1][self.notification_attr]
# 				if user['notification_id'] in user['notifications']:
# 					self.log.debug("User already been notified")
# 					continue
# 				yield user
# 			except KeyError:
# 				self.log.warn("Cannot Notify User. " + 
# 							  "A necessary Attribute is missing " + 
# 							  u[0])