import os
import socket
import edir_reminder_service.utils as utils
from StringIO import StringIO
import logging
log = logging.getLogger('edir-reminder-server')

DEBUG = utils.str2bool(os.environ.get('DEBUG', "false"))

SERVICE_NAME = "eDir Login/Password Email Reminder Service"
HOSTNAME = socket.gethostname()

# set defaults
default_cfg = StringIO("""\
[common]
server = ldap://localhost
bind_dn =
bind_password =
start_tls = false
ignore_cert = false
base_context = 
expiry_attribute = passwordExpirationTime
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
    
    c['server'] = config.get("common", "server").strip()
    c['bind_dn'] = config.get("common", "bind_dn").strip()
    c['bind_password'] = config.get("common", "bind_password").strip()
    c['start_tls'] = config.getboolean("common", "start_tls")
    c['ignore_cert'] = config.getboolean("common", "ignore_cert")
    c['base_context'] = config.get("common", "base_context").strip()
    c['expiry_attribute'] = config.get("common", "expiry_attribute").strip()
    c['notify_attribute'] = config.get("common", "notify_attribute").strip()
    c['mail_server_address'] = config.get("common", "mail_server_address").strip()
    c['log_file_path'] = config.get("common", "log_file_path").strip()
    
    c['admin'] = {}
    c['admin']['from_address'] = config.get("admin", "from_address").strip()
    c['admin']['to_address'] = config.get("admin", "to_address").strip()
    c['admin']['from_text'] = config.get("admin", "from_text").strip()
    c['admin']['subject'] = config.get("admin", "subject").strip()
    c['admin']['filename'] = config.get("admin", "filename").strip()
    
    c['test'] = {}
    c['test']['test_mode'] = config.getboolean("test", "test_mode")
    c['test']['to_address'] = config.get("test", "to_address").strip()
    c['test']['send_message'] = config.getboolean("test", "send_message")
    c['test']['restrict'] = config.getboolean("test", "restrict")
    c['test']['users'] = list(user for user_list in map(lambda s: s.split(' '), config.get("test", "users", "").split('\n')) for user in user_list)
    
    c['rules'] = []
    for section in config.sections():
        try:
            rule_num = int(section)
        except ValueError:
            continue

        c['rules'].append({
            "days": rule_num,
            "from_address": config.get(section, "from_address", "root@" + HOSTNAME).strip() if config.has_option(section, "from_address") else "root@" + HOSTNAME,
            "from_text": config.get(section, "from_text").strip() if config.has_option(section, "from_text") else SERVICE_NAME,
            "subject": config.get(section, "subject").strip() if config.has_option(section, "subject") else "Login will expire soon",
            "filename": config.get(section, "filename").strip() if config.has_option(section, "filename") else os.path.dirname(__file__) + "/templates/notify.tmpl"
        })

    c['rules'] = sorted(c['rules'], key=lambda r: r['days'], reverse=True)
    
    # compute time interval [start:end[ of each rule
    from datetime import timedelta, datetime
    now = datetime.utcnow()
    prev_rule = None
    for rule in c['rules']:
        start = now + timedelta(days=rule['days'])
        if prev_rule:
            prev_rule['end'] = start.strftime('%Y%m%d%H%M%SZ')
        rule['start'] = start.strftime('%Y%m%d%H%M%SZ')
        prev_rule = rule
    if prev_rule:
        prev_rule['end'] = now.strftime('%Y%m%d%H%M%SZ')
        
    log.debug(repr(c['rules']))

    return utils.obj(c)