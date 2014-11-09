[![Build Status](https://travis-ci.org/sttts/ldap-notify.svg)](https://travis-ci.org/sttts/ldap-notify)

ldap-notify
===========

ldap-notify searches users in an LDAP directory whose login or password expires in a certain number of days. These users are notified with a customizable email. The time intervals for the notifications and the email templates can be freely defined. By using a custom LDAP attribute the last notification is stored in the directory such that users are only notified once per rule. Moreover, this mechanism allows running the tool (e.g. via cron) on multiple machine with a certain time delta in order to implement high availabiliy. 



## Configuration ##

The behaviour of ldap-notify is defined via a configuration file and its values are optionally overwritten by command line arguments:

```
Usage: ldap-notify [OPTION]... -c <config_file.conf>

Parameters:'
  -h, --help                    show this help
  -c, --conf                    mandatory parameter: the config file name
  -k                            ignore SSL/TLS certificates
  --dry                         do not send emails or modify anything in ldap
  --test <test-address>         send all mails to the given address
  --restrict <DN>;<CN>;...      restrict notifications to these semicolon 
                                separated user DNs or CNs
  --time <timestamp>            simulate current UTC time (format: 20141031162633Z)
  -v, --verbose                 verbose logging
  -d, --debug                   debug logging
  --print-conf                  print the used configuration to console and exit
```

The configuration file given by the mandatory ```-c``` or ```--conf``` option uses the common INI file format. This means that it consists of sections with values in the format

```
[section_name]
attribute=value
second_attribute = multi
    line
    value
```

The default configuration is the following:

```
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
from_address = root@<HOSTNAME>
to_address = admin@<HOSTNAME>
from_text = Login/Password Expiry Notification
subject = Login will expire soon
text_template = <LDAP_NOTIFY_DIR>/templates/admin.tmpl.txt

[test]
enabled = false
to_address = root@<HOSTNAME>
```

## Rules ##

The tool is meant to be launched daily e.g. using the cron service on a Linux server. It reads rule definition from a configuration file. Each rule consists of:

- _a number of days_, which at the same time is also the name of the rule
- _from\_address_, an email address used as sender address
