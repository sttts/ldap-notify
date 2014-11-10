import sys
import os
import logging as log
import getopt
import ConfigParser
import ldap
import locale
from datetime import datetime
from smtplib import SMTPException

import ldap_notify.config
import ldap_notify.connection
from ldap_notify import ConfigError
import ldap_notify.globals as g

# add virtualenv path to PYTHON_PATH, so libs are found
virtualenv_path = os.path.dirname(__file__) + '/env'
if virtualenv_path not in sys.path:
	sys.path.insert(0, virtualenv_path)

class SysExitException(Exception):
	def __init__(self, rc):
		super(SysExitException, self).__init__('sys.exit(%i)' % rc)
		self.rc = rc

def usage(): 
	print """Usage: ldap-notify [OPTION]... -c <config_file.conf>

Parameters:'
  -h, --help                    show this help
  -c, --conf                    mandatory parameter: the config file name
  -k                            ignore SSL/TLS certificates
  --dry                         do not send emails or modify anything in ldap
  --test <test-address>         send all mails to the given address
  --restrict <DN>;<CN>;...      restrict notifications to these semicolon 
                                separated user DNs or CNs
  --time <timestamp>            simulate current UTC time (format: 20141031162633Z)
  -v, --verbose                 verbose logging
  -d, --debug                   debug logging
  --print-conf                  print the used configuration to console and exit
"""

def run(config):
	# start the algorithm
	con = ldap_notify.connection.connect_to_ldap(config)
	import ldap_notify.algorithm as algorithm
	if g.DEBUG > 5:
		print repr(algorithm.search_users(config, con))
	
	# process the rules, starting with the smallest interval
	users_without_email = []
	failed_users = []
	notified_users = []
	for rule in config.rules:
		rule_users = algorithm.users_for_rule(config, con, rule)
		
		# assign rule
		for user in rule_users:
			setattr(user, 'rule', rule)
		
		# notify those which have an email
		successful, failed = algorithm.notify_users(config, con, filter(lambda u: u.mail, rule_users), rule)
		notified_users.extend(successful)
		failed_users.extend(failed)
		
		# collect all others for the admin
		users_without_email.extend(filter(lambda u: not u.mail, rule_users))

	# find users without graceLogins
	users_without_grace_logins = algorithm.search_users_without_grace_logins(config, con)

	# send admin email
	algorithm.notify_admin(config, con, notified_users, failed_users, users_without_email, users_without_grace_logins)

def main(argv):
	try:
		locale.setlocale(locale.LC_ALL, "")
	
		# default values
		ignore_cert = None
		config_file = None
		debug = 0
		verbose = False
		now = datetime.utcnow()
		dry = None
		test = None
		test_address = None
		restrict_to_users = None
		print_conf = None
		config_file = None
	
		# parse arguments	
		try:
			opts, args = getopt.getopt(argv, "hc:dvk", ["help", "config=", "time=", "test=", 'dry', "debug", "verbose", "restrict=", "print-conf"])
		except getopt.GetoptError:
			usage()
			raise SysExitException(2)
		for opt, arg in opts:
			if opt in ['-h', '--help']:
				usage()
				raise SysExitException(0)
			elif opt in ['--test']:
				test = True
				test_address = arg
			elif opt in ['--dry']:
				dry = True
			elif opt in ['-d', '--debug']:
				debug += 1
			elif opt in ['-v', '--verbose']:
				verbose = True
			elif opt in ['-c', '--conf']:
				config_file = arg
			elif opt in ['--time']:
				now = datetime.strptime(arg, g.LDAP_TIME_FORMAT)
			elif opt in ['-k']:
				ignore_cert = True
			elif opt in ['--restrict']:
				restrict_to_users = arg
			elif opt in ['--print-conf']:
				print_conf = True

		# no args allow other than options
		if args:
			usage()
			return 2
			
		# set globals
		g.DEBUG = debug
		g.VERBOSE = verbose
		g.NOW = now

		# setup logging
		log.basicConfig(level=log.DEBUG if g.DEBUG else log.INFO if g.VERBOSE else log.WARN,
					format='%(asctime)s %(levelname)s: %(message)s')

		# load configuration
		preconfig = ldap_notify.config.load(filename=config_file)
		
		# merge config with values from command line
		if ignore_cert!=None:      preconfig.set('common', 'ignore_cert', 'true' if ignore_cert else 'false')
		if dry!=None:              preconfig.set('common', 'dry', 'true' if dry else 'false')
		if test!=None:             preconfig.set('test', 'enabled', 'true' if test else 'false')
		if test_address!=None:     preconfig.set('test', 'to_address', test_address)
		if restrict_to_users!=None:preconfig.set('common', 'restrict_to_users', restrict_to_users)

		# evaluate config_file
		config = ldap_notify.config.evaluate(preconfig)
		log.debug('dry = %s, %s' % (str(dry), str(config.dry)))

		# print config only?
		if print_conf:
			import StringIO
			f = StringIO.StringIO()
			preconfig.write(f)
			print f.getvalue()
			return 0
		
		# only proceed if a config_file was given. Especially --print-conf should work without
		if not config_file:
			usage()
			return 2

		# the actual code doing stuff
		run(config)

	except ConfigParser.NoOptionError, e:
		print >> sys.stderr, "Configuration error: %s" % str(e)
		return 2
	except ConfigError, e:
		print >> sys.stderr, "Configuration error: %s" % str(e)
		return 2
	except ldap.LDAPError, e:
		msg = e.args[0]['desc'] if 'desc' in e.args[0] else str(e)
		print >> sys.stderr, "LDAP error: %s" % msg
		return 1
	except SMTPException, e:
		print >> sys.stderr, "SMTP error: %s" % str(e)
		return 1
	except KeyboardInterrupt:
		return 253
	except SysExitException, e:
		return e.rc
	else:
		return 0

# run app in standalone mode
if __name__ == "__main__":
	rc = main(sys.argv[1:])
	sys.exit(rc)
