#!/usr/bin/env python
import sys
import os
import logging as log
import getopt
import ConfigParser
import ldap
from datetime import datetime

import edir_reminder_service.config
import edir_reminder_service.connection

# add virtualenv path to PYTHON_PATH, so libs are found
virtualenv_path = os.path.dirname(__file__) + '/env'
if virtualenv_path not in sys.path:
	sys.path.insert(0, virtualenv_path)

def usage(): 
	print """
Usage: edit-reminder-server [OPTION]... -c <config_file.conf>

Parameters:'
  -h, --help                  show this help
  -c, --conf                  mandatory parameter: the config file name
  -k                          ignore SSL/TLS certificates
  --dry                       do not send emails, only log what would be done without --dry
  -v, --verbose               verbose logging
  -d, --debug                 debug logging
  -t, --time                  simulate current UTC time (format: 20141031162633Z)
"""

def main(argv):
	import edir_reminder_service.globals as g

	# default values
	ignore_cert = False
	config_file = None

	# parse arguments	
	try:
		opts, args = getopt.getopt(argv, "hc:t:dvkt", ["help", "config=", "time=", "dry", "debug", "verbose"])
	except getopt.GetoptError:
		usage()
		sys.exit(2)
	for opt, arg in opts:
		if opt in ('-h', '--help'):
			usage()
			sys.exit()
		elif opt in ('--dry', ):
			g.DRY_RUN = True
		elif opt in ('-d', '--debug'):
			g.DEBUG += 1
		elif opt in ('-v', '--verbose'):
			g.VERBOSE = True
		elif opt in ('-c', '--conf'):
			config_file = arg
		elif opt in ('-t', '--time'):
			g.NOW = datetime.strptime(arg, g.LDAP_TIME_FORMAT)
		elif opt in ('-k', ):
			ignore_cert = True

	if not config_file or args:
		usage()
		sys.exit(2)
		
	# setup logging
	log.basicConfig(level=log.DEBUG if g.DEBUG else log.INFO if g.VERBOSE else log.WARN,
				format='%(asctime)s %(levelname)s: %(message)s')

	try:
		# load configuration
		config = edir_reminder_service.config.load(filename=config_file)
		
		# overwrite values from command line
		config.ignore_cert = config.ignore_cert or ignore_cert

		# start the algorithm
		con = edir_reminder_service.connection.connect_to_ldap(config)
		import edir_reminder_service.algorithm as algorithm
		if g.DEBUG > 5:
			print repr(algorithm.search_users(config, con))
		for rule in config.rules:
			users, skipped = algorithm.users_for_rule(config, con, rule)
			for user in users:
				algorithm.mark_user_notified(config, con, user, rule)

	except ConfigParser.NoOptionError, e:
		print >> sys.stderr, "Configuration error: %s" % str(e)
		sys.exit(2)
	except ldap.LDAPError, e:
		msg = e.args[0]['desc'] if 'desc' in e.args[0] else str(e)
		print >> sys.stderr, "LDAP error: %s" % msg
		sys.exit(2)
	#except Exception, e:
	#	print >> sys.stderr, "Error: %s" % str(e)
	#	sys.exit(2)
	except KeyboardInterrupt:
		sys.exit(253)

# run app in standalone mode
if __name__ == "__main__":
	main(sys.argv[1:])