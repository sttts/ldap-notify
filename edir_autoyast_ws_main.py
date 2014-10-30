#!/usr/bin/env python
import sys
import os
import logging as log

# add virtualenv path to PYTHON_PATH, so libs are found
virtualenv_path = os.path.dirname(__file__) + '/env'
if virtualenv_path not in sys.path:
	sys.path.insert(0, virtualenv_path)

# setup logging
log.basicConfig(level=log.DEBUG if os.environ.get('DEBUG') else log.INFO,
	format='%(asctime)s %(filename)s:%(lineno)d %(funcName)s() [%(name)s] %(levelname)s: %(message)s')

# run app in standalone mode
if __name__ == "__main__":
	#from edir_reminder_service import config
	#app.run(debug=config.DEBUG, host=config.LISTEN[0], port=config.LISTEN[1])
	pass