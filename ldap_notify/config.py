import os
import socket
from StringIO import StringIO
import logging
log = logging.getLogger('ldap-notify.config')

from ldap_notify import ConfigError
import ldap_notify.utils as utils
import ldap_notify.globals as g

SERVICE_NAME = "Login/Password Expiry Notification"
HOSTNAME = socket.gethostname()

# set defaults
default_cfg = """\
[common]
server = ldap://localhost
bind_dn =
bind_password =
bind_password_base64 =
starttls = false
ignore_cert = false
base_context = 
expiry_attribute = passwordExpirationTime
notify_attribute = pwmNotify
mail_server_address = localhost
log_file_path = /dev/stdout
dry = false
restrict_to_users =
user_objectclass = person

[smtp]
server =
ssl = false
starttls = false
user =
password =
password_base64 =

[admin]
from_address = {root_mail!s}
to_address = {admin_mail!s}
from_text = {service_name!s}
subject = Login will expire soon
text_template = {text_template!s}

[test]
enabled = false
to_address = {root_mail!s}
""".format(
    root_mail="root@" + HOSTNAME,
    admin_mail="admin@" + HOSTNAME,
    service_name=SERVICE_NAME,
    text_template=os.path.dirname(__file__) + "/templates/admin.tmpl.txt"
)

def flatten(l):
    return list(x for sublist in l for x in sublist)

def restrict_user_list_parse(s):
    lst = s.replace(';', '\n').replace(' ', '\n').split('\n')
    return set(filter(None, lst))

# load config file
def load(filename = None):
    import ConfigParser
    config_file = ConfigParser.SafeConfigParser()
    config_file.readfp(StringIO(default_cfg))
    if filename:
        log.info('Reading config file %s' % filename)
        config_file.readfp(open(filename))
    
    return config_file

def evaluate(config):
    c = {}
    
    c['server'] = config.get("common", "server").strip() or None
    c['bind_dn'] = config.get("common", "bind_dn").strip() or None
    c['bind_password'] = config.get("common", "bind_password").strip() or None
    c['bind_password_base64'] = config.get("common", "bind_password_base64").strip() or None
    c['starttls'] = config.getboolean("common", "starttls")
    c['ignore_cert'] = config.getboolean("common", "ignore_cert")
    c['base_context'] = config.get("common", "base_context").strip() or None
    c['expiry_attribute'] = config.get("common", "expiry_attribute").strip() or None
    c['notify_attribute'] = config.get("common", "notify_attribute").strip() or None
    c['user_objectclass'] = config.get("common", "user_objectclass").strip() or None
    c['log_file_path'] = config.get("common", "log_file_path").strip() or None
    c['dry'] = config.getboolean("common", "dry")
    c['restrict_to_users'] = restrict_user_list_parse(config.get("common", "restrict_to_users", "").strip())
    
    c['smtp'] = {}
    c['smtp']['server'] = config.get("smtp", "server").strip() or None
    c['smtp']['ssl'] = config.getboolean("smtp", "ssl")
    c['smtp']['starttls'] = config.getboolean("smtp", "starttls")
    c['smtp']['user'] = config.get("smtp", "user").strip() or None
    c['smtp']['password'] = config.get("smtp", "password").strip() or None
    c['smtp']['password_base64'] = config.get("smtp", "password_base64").strip() or None
    
    c['admin'] = {}
    c['admin']['from_address'] = config.get("admin", "from_address").strip() or None
    c['admin']['to_address'] = config.get("admin", "to_address").strip() or None
    c['admin']['from_text'] = config.get("admin", "from_text").strip() or None
    c['admin']['subject'] = config.get("admin", "subject").strip() or None
    c['admin']['text_template'] = config.get("admin", "text_template").strip() or None
    
    c['test'] = {}
    c['test']['enabled'] = config.getboolean("test", "enabled")
    c['test']['to_address'] = config.get("test", "to_address").strip() or None
    
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
    
    # decode base64 passwords, if set
    import base64
    if c['bind_password'] and c['bind_password_base64']:
        raise ConfigError('Cannot set bind_password and bind_password_base64')
    if not c['bind_password'] and c['bind_password_base64']:
        c['bind_password'] = base64.b64decode(c['bind_password_base64'])

    if c['smtp']['password'] and c['smtp']['password_base64']:
        raise ConfigError('Cannot set SMTP password and password_base64')
    if not c['smtp']['password'] and c['smtp']['password_base64']:
        c['smtp']['password'] = base64.b64decode(c['smtp']['password_base64'])
    
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
