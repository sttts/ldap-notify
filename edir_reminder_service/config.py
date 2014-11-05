import os
import socket
from StringIO import StringIO
import logging
log = logging.getLogger('edir-reminder-server')

import edir_reminder_service.utils as utils
import edir_reminder_service.globals as g

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

[smtp]
server =
ssl = false
starttls = false
user =
password =

[admin]
from_address = {root_mail!s}
to_address = {admin_mail!s}
from_text = {service_name!s}
subject = Login will expire soon
text_template = {text_template!s}

[test]
dry = false
test = false
to_address = {root_mail!s}
send_message = true
restrict = false
restrict_to_users =
""".format(
    root_mail="root@" + HOSTNAME,
    admin_mail="admin@" + HOSTNAME,
    service_name=SERVICE_NAME,
    text_template=os.path.dirname(__file__) + "/templates/admin.tmpl.txt"
))

# load config file
def load(filename = "login.conf"):
    import ConfigParser
    config = ConfigParser.SafeConfigParser()
    config.readfp(default_cfg)
    
    if filename:
        log.info('Reading config file %s' % filename)
        config.read(filename)
    
    c = {}
    
    c['server'] = config.get("common", "server").strip()
    c['bind_dn'] = config.get("common", "bind_dn").strip()
    c['bind_password'] = config.get("common", "bind_password").strip()
    c['start_tls'] = config.getboolean("common", "start_tls")
    c['ignore_cert'] = config.getboolean("common", "ignore_cert")
    c['base_context'] = config.get("common", "base_context").strip()
    c['expiry_attribute'] = config.get("common", "expiry_attribute").strip()
    c['notify_attribute'] = config.get("common", "notify_attribute").strip()
    c['log_file_path'] = config.get("common", "log_file_path").strip()
    
    c['smtp'] = {}
    c['smtp']['server'] = config.get("smtp", "server").strip()
    c['smtp']['ssl'] = config.getboolean("smtp", "ssl")
    c['smtp']['starttls'] = config.getboolean("smtp", "starttls")
    c['smtp']['user'] = config.get("smtp", "user").strip()
    c['smtp']['password'] = config.get("smtp", "password").strip()
    
    c['admin'] = {}
    c['admin']['from_address'] = config.get("admin", "from_address").strip()
    c['admin']['to_address'] = config.get("admin", "to_address").strip()
    c['admin']['from_text'] = config.get("admin", "from_text").strip()
    c['admin']['subject'] = config.get("admin", "subject").strip()
    c['admin']['text_template'] = config.get("admin", "text_template").strip()
    
    c['test'] = {}
    c['test']['test'] = config.getboolean("test", "test")
    c['test']['dry'] = config.getboolean("test", "dry")
    c['test']['to_address'] = config.get("test", "to_address").strip()
    c['test']['send_message'] = config.getboolean("test", "send_message")
    c['test']['restrict'] = config.getboolean("test", "restrict")
    c['test']['restrict_to_users'] = list(user for user_list in map(lambda s: s.split(' '), config.get("test", "restrict_to_users", "").split('\n')) for user in user_list)
    
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
            "text_template": config.get(section, "text_template").strip() if config.has_option(section, "text_template") else os.path.dirname(__file__) + "/templates/notify.tmpl.txt",
            "html_template": config.get(section, "html_template").strip() if config.has_option(section, "html_template") else None
        })

    c['rules'] = sorted(c['rules'], key=lambda r: r['days'])
    
    # compute time interval [start:end[ of each rule
    from datetime import timedelta
    start = g.NOW
    for rule in c['rules']:        
        rule['start'] = start.strftime(g.LDAP_TIME_FORMAT)
        end = g.NOW + timedelta(days=rule['days'])
        rule['end'] = end.strftime(g.LDAP_TIME_FORMAT)
        
        start = end
        
    log.debug(repr(c['rules']))

    return utils.obj(c)