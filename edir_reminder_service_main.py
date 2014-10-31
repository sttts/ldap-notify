#!/usr/bin/env python
import sys
import os
import logging as log
import getopt
import ConfigParser
import ldap
import json

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
"""

def main(argv):
	# default values
	config_file = None
	global DRY_RUN
	DRY_RUN = False
	global DEBUG
	DEBUG = 0
	global VERBOSE
	VERBOSE = False
	global IGNORE_CERT
	IGNORE_CERT = False

	# parse arguments	
	try:
		opts, args = getopt.getopt(argv, "dhc:vk", ["help", "config=", "dry", "debug", "verbose"])
	except getopt.GetoptError:
		usage()
		sys.exit(2)
	for opt, arg in opts:
		if opt in ('-h', '--help'):
			usage()
			sys.exit()
		elif opt in ('--dry', ):
			DRY_RUN = True
		elif opt in ('-d', '--debug'):
			DEBUG += 1
		elif opt in ('-v', '--verbose'):
			VERBOSE = True
		elif opt in ('-c', '--conf'):
			config_file = arg
		elif opt in ('-k',):
			IGNORE_CERT = True

	if not config_file or args:
		usage()
		sys.exit(2)
		
	# setup logging
	log.basicConfig(level=log.DEBUG if DEBUG else log.INFO if VERBOSE else log.WARN,
				format='%(asctime)s %(filename)s:%(lineno)d %(funcName)s() [%(name)s] %(levelname)s: %(message)s')
	
	# load configuration
	try:
		config = edir_reminder_service.config.load(config_file)
	except ConfigParser.NoOptionError, e:
		print >> sys.stderr, "Configuration error: %s" % str(e)
		sys.exit(2)
		
	# overwrite values from command line
	config.ignore_cert = config.ignore_cert or IGNORE_CERT
		
	# start the algorithm
	try:
		con = edir_reminder_service.connection.connect_to_ldap(config)
		import edir_reminder_service.algorithm as algorithm
		for rule in config.rules:
			users = algorithm.users_for_rule(config, con, rule)
			if DEBUG > 1:
				print json.dumps({'days': rule.days, 'users': users}, sort_keys=True, indent=4, separators=(',', ': '))
	except ldap.LDAPError, e:
		msg = e.args[0]['desc'] if 'desc' in e.args[0] else str(e)
		print >> sys.stderr, "LDAP error: %s" % msg
		sys.exit(2)
	except KeyboardInterrupt:
		sys.exit(253)

# run app in standalone mode
if __name__ == "__main__":
	main(sys.argv[1:])