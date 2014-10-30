#!/usr/bin/env python
import sys
import os
import logging as log
import getopt
import ConfigParser
import ldap

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
  --dry                   do not send emails, only log what would be done without -d
"""

def main(argv):
	# default values
	config_file = None
	global DRY_RUN
	DRY_RUN = False
	global DEBUG
	DEBUG = os.environ.get('DEBUG', False)

	# parse arguments	
	try:
		opts, args = getopt.getopt(argv, "hc:d", ["help", "config=", "dry", "--debug"])
	except getopt.GetoptError:
		usage()
		sys.exit(2)
	for opt, arg in opts:
		if opt in ("-h", "--help"):
			usage()
			sys.exit()
		elif opt in ('--dry'):
			DRY_RUN = True
		elif opt in ('-d','--debug'):
			DEBUG = True
		elif opt in ('-c', '--conf'):
			config_file = arg

	if not config_file or args:
		usage()
		sys.exit(2)
		
	# setup logging
	log.basicConfig(level=log.DEBUG if DEBUG else log.WARN,
				format='%(asctime)s %(filename)s:%(lineno)d %(funcName)s() [%(name)s] %(levelname)s: %(message)s')
	
	# load configuration
	try:
		config = edir_reminder_service.config.load(config_file)
	except ConfigParser.NoOptionError, e:
		print >> sys.stderr, "Configuration error: %s" % str(e)
		sys.exit(2)
		
	# start the algorithm
	try:
		con = edir_reminder_service.connection.connect_to_ldap(config)
	except ldap.LDAPError, e:
		print >> sys.stderr, "Cannot connect to the LDAP server: %s" % str(e)
		sys.exit(2)

# run app in standalone mode
if __name__ == "__main__":
	main(sys.argv[1:])