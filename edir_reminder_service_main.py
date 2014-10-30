#!/usr/bin/env python
import sys
import os
import logging as log
import getopt
import edir_reminder_service.config
import ConfigParser

# add virtualenv path to PYTHON_PATH, so libs are found
virtualenv_path = os.path.dirname(__file__) + '/env'
if virtualenv_path not in sys.path:
	sys.path.insert(0, virtualenv_path)

# setup logging
log.basicConfig(level=log.DEBUG if os.environ.get('DEBUG') else log.INFO,
	format='%(asctime)s %(filename)s:%(lineno)d %(funcName)s() [%(name)s] %(levelname)s: %(message)s')

def usage(): 
	print('Usage: edit-reminder-server [OPTION]... -c <config_file.conf>')

def main(argv):
	# default values
	config_file = None
	global DRY_RUN
	DRY_RUN = False

	# parse arguments	
	try:
		opts, args = getopt.getopt(argv, "hc:d", ["help", "config=", "dry"])
	except getopt.GetoptError:
		usage()
		sys.exit(2)
	for opt, arg in opts:
		if opt in ("-h", "--help"):
			usage()
			sys.exit()
		elif opt in ('-d', '--dry'):
			DRY_RUN = True
		elif opt in ('-c', '--conf'):
			config_file = arg

	if not config_file or args:
		usage()
		sys.exit(2)
		
	# load configuration
	try:
		config = edir_reminder_service.config.load(config_file)
	except ConfigParser.NoOptionError, e:
		print >> sys.stderr, "Configuration error: %s" % str(e)
		sys.exit(2)

# run app in standalone mode
if __name__ == "__main__":
	main(sys.argv[1:])