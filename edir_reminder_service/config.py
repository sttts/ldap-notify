import os
import socket
import edir_reminder_service.utils as utils
from StringIO import StringIO

DEBUG = utils.str2bool(os.environ.get('DEBUG', "false"))

SERVICE_NAME = "eDir Login/Password Email Reminder Service"
HOSTNAME = socket.gethostname()

# set defaults
default_cfg = StringIO("""\
[common]
server = ldap://localhost
base_context = 
notify_attribute = pwmNotify
mail_server_address = localhost
log_file_path = /dev/stdout

[admin]
from_address = {root_mail!s}
to_address = {admin_mail!s}
from_text = {service_name!s}
subject = Login will expire soon
filename = {admin_filename!s}

[test]
test_mode = false
to_address = {root_mail!s}
send_message = true
restrict = false
users =
""".format(
    root_mail="root@" + HOSTNAME,
    admin_mail="admin@" + HOSTNAME,
    service_name=SERVICE_NAME,
    admin_filename=os.path.dirname(__file__) + "/templates/admin.tmpl"
))

# load config file
def load(filename = "login.conf"):
    import ConfigParser
    config = ConfigParser.SafeConfigParser()
    config.readfp(default_cfg)
    config.read('login.conf')
    
    c = {}
    
    c['server'] = config.get("common", "server")
    c['base_context'] = config.get("common", "base_context")
    c['notify_attribute'] = config.get("common", "notify_attribute")
    c['mail_server_address'] = config.get("common", "mail_server_address")
    c['log_file_path'] = config.get("common", "log_file_path")
    
    c['admin'] = {}
    c['admin']['from_address'] = config.get("admin", "from_address")
    c['admin']['to_address'] = config.get("admin", "to_address")
    c['admin']['from_text'] = config.get("admin", "from_text")
    c['admin']['subject'] = config.get("admin", "subject")
    c['admin']['filename'] = config.get("admin", "filename")
    
    c['test'] = {}
    c['test']['test_mode'] = config.getboolean("test", "test_mode")
    c['test']['to_address'] = config.get("test", "to_address")
    c['test']['send_message'] = config.getboolean("test", "send_message")
    c['test']['restrict'] = config.getboolean("test", "restrict")
    c['test']['users'] = list(user for user_list in map(lambda s: s.split(' '), config.get("test", "users", "").split('\n')) for user in user_list)
    
    c['rules'] = {}
    for section in config.sections():
        try:
            rule_num = int(section[7:])
            c['rules'][rule_num] = {
                "days": rule_num,
                "from_address": config.get(section, "from_address", "root@" + HOSTNAME) if config.has_option(section, "from_address") else False,
                "from_text": config.get(section, "from_text") if config.has_option(section, "from_text") else SERVICE_NAME,
                "subject": config.get(section, "subject") if config.has_option(section, "subject") else "Login will expire soon",
                "filename": config.get(section, "filename") if config.has_option(section, "filename") else os.path.dirname(__file__) + "/templates/notify.tmpl"
            }
        except:
            continue

    return utils.obj(c)