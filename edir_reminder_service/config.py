import os
import socket
from edir_reminder_service.utils import str2bool

DEBUG = str2bool(os.environ.get('DEBUG', "false"))

SERVICE_NAME = "eDir Login/Password Email Reminder Service"
HOSTNAME = socket.gethostname()

# load config file
import ConfigParser
config = ConfigParser.SafeConfigParser()
config.read('login.conf')

SERVER = config.get("common", "Server", "ldap://localhost")
BASE_CONTEXT = config.get("common", "BaseContext", "")
NOTIFY_ATTRIBUTE = config.get("common", "NotifyAttribute", "pwmNotify")
MAIL_SERVER_ADDRESS = config.get("common", "MailServerAddress", "localhost")
LOG_FILE_PATH = config.get("common", "LogFilePath", "/dev/stdout")

ADMIN_FROM_EMAIL_ADDRESS = config.get("admin", "FromEmailAddress", "root@" + HOSTNAME)
ADMIN_TO_EMAIL_ADDRESS = config.get("admin", "ToAddress", "admin@" + HOSTNAME)
ADMIN_FROM_TEXT = config.get("admin", "FromText", SERVICE_NAME)
ADMIN_SUBJECT = config.get("admin", "Subject", "Login will expire soon")
ADMIN_FILENAME = config.get("admin", "Filename", os.path.dirname(__file__) + "/templates/admin.tmpl")

TEST_TESTMODE = config.getboolean("test", "Testmode", False)
TEST_TO_EMAIL_ADDRESS = config.get("test", "ToAddress", "root@" + HOSTNAME)
TEST_SEND_MESSAGE = config.getboolean("test", "sendmessage", False)
TEST_RESTRICT = config.getboolean("test", "restrict", False)

# read rules
RULES = {}
for section in config.sections():
    if section.startswith("notify-"):
        rule_num = int(section[7:])
        RULES[rule_num] = {
            "FromEmailAddress": config.get(section, "FromEmailAddress", "root@" + HOSTNAME),
            "FromText": config.get(section, "FromText", SERVICE_NAME),
            "Subject": config.get(section, "Subject", "Login will expire soon"),
            "Days": config.getint(section, "days", 30),
            "Filename": config.get(section, "Filename",os.path.dirname(__file__) + "/templates/notify.tmpl" )
        }