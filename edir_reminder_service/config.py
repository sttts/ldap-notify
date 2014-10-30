import os
import socket
import edir_reminder_service.utils as utils

DEBUG = utils.str2bool(os.environ.get('DEBUG', "false"))

SERVICE_NAME = "eDir Login/Password Email Reminder Service"
HOSTNAME = socket.gethostname()

# load config file
def load(filename = "login.conf"):
    import ConfigParser
    config = ConfigParser.SafeConfigParser()
    config.read('login.conf')
    
    c = {}
    
    c['server'] = config.get("common", "Server", "ldap://localhost")
    c['base_context'] = config.get("common", "BaseContext", "")
    c['notify_attribute'] = config.get("common", "NotifyAttribute", "pwmNotify")
    c['mail_server_address'] = config.get("common", "MailServerAddress", "localhost")
    c['log_file_path'] = config.get("common", "LogFilePath", "/dev/stdout")
    
    c['admin'] = {}
    c['admin']['from_email_address'] = config.get("admin", "FromEmailAddress", "root@" + HOSTNAME)
    c['admin']['to_email_address'] = config.get("admin", "ToAddress", "admin@" + HOSTNAME)
    c['admin']['from_text'] = config.get("admin", "FromText", SERVICE_NAME)
    c['admin']['subject'] = config.get("admin", "Subject", "Login will expire soon")
    c['admin']['filename'] = config.get("admin", "Filename", os.path.dirname(__file__) + "/templates/admin.tmpl")
    
    c['test'] = {}
    c['test']['testmode'] = config.getboolean("test", "Testmode", False)
    c['test']['to_email_address'] = config.get("test", "ToAddress", "root@" + HOSTNAME)
    c['test']['send_message'] = config.getboolean("test", "sendmessage", False)
    c['test']['restrict'] = config.getboolean("test", "restrict", False)
    c['test']['users'] = filter(None, config.get("test", "user", "").split('\n').split(' '))
    
    c['rules'] = {}
    for section in config.sections():
        if section.startswith("notify-"):
            rule_num = int(section[7:])
            c['rules'][rule_num] = {
                "FromEmailAddress": config.get(section, "FromEmailAddress", "root@" + HOSTNAME),
                "FromText": config.get(section, "FromText", SERVICE_NAME),
                "Subject": config.get(section, "Subject", "Login will expire soon"),
                "Days": config.getint(section, "days", 30),
                "Filename": config.get(section, "Filename",os.path.dirname(__file__) + "/templates/notify.tmpl" )
            }
            
    return utils.obj(c)