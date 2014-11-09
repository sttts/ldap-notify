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

The configuration file given by the mandatory ```-c``` or ```--conf``` option uses the common INI file format. This means that it consists of sections with values in the format:

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

The configuration options have the following meaning:

| Section | Option  | Format   | Description | Examples |
| ------- |:------- |:-------- |:----------- |:---------|
| common  | server  | RFC 4516 | the server LDAP URI | ldap://host:389 or ldaps://host |
| common  | bind_dn | DN or empty | the DN to bind to; can be empty | cn=admin,ou=users,dc=localhost |
| common  | bind_password | string | the password to be used during binding | secret |
| common  | bind_password_base64 | base64 encoded string | an encoded bind password | YWRtaW5fc2VjcmV0 |
| common  | starttls | boolean | use starttls on a ldap:// connection | true or false |
| common  | ignore_cert | boolean | don't check server SSL/TLS certificate | true or false |
| common  | base_context | DN or empty | the base DN to start a subtree search at | ou=users,dc=localhost or empty for the root context |
| common  | expiry_attribute | LDAP attribute | the attribute holding the expiration timestamp | passwordExpirationTime |
| common  | notify_attribute | LDAP attribute | the attribute used to store sent notifications | pwmNotify |
| common  | dry | boolean | If true, no mails are actually sent and no LDAP modifications take place. Can be overwritten with ```--dry```on the command line. | true or false |
| common  | restrict_to_users | DN or CN list, separated by semi-colon, space, or newline | restrict actual sent mails and LDAP modification to the given CNs or DNs. Useful for testing | cn=admin,ou=users,dc=localhost;root;hschmidt; |
| common  | user_objectclass | LDAP objectClass | an object class name to restrict the user search | pwmUser or person |
| smtp    | server | HOSTNAME[:PORT] | the mail server address | smtp.gmail.com |
| smtp    | ssl | boolean | true if the server speaks SSL | true or false |
| smtp    | starttls | boolean | use starttls after connecting with encryption | true or false |
| smtp    | user | string | the SMTP user name to authenticate with | hschmidt |
| smtp    | password | string | the SMTP password to authenticate with | secret |
| smtp    | password_base64 | base64 encoded string | the SMTP password encoded with base64 | YWRtaW5fc2VjcmV0 |
| admin   | from_address | email address | the sender email address for the admin report | admin@company.com |
| admin   | to_address | email address | the recepient email address for the admin report | admin_group@company.com |
| admin   | from_text | sender name | the sender name for the admin report | Password Expiry Notification Service |
| admin   | subject | string | the admin report subject | Password Expiry Notification Report |
| admin   | text_template | absolute filename | the admin report email body template | /etc/ldap-notify/admin.tmpl.txt |
| test    | enabled | boolean | if true, all emails are sent to the test email address | true or false |
| test    | to_address | email address | the test email address | root@localhost |

## Rules ##

An arbitrary number of rules can be defined in the configuration file. The rules are named according to their number of days before an expiration date when the rule applies. E.g. a 30 day rule is called "30".

The default values of a 30 day rule:

```
[30]
from_address = <ADMIN FROM ADRESS>
from_text = <ADMIN FROM TEXT>
subject = Login will expire soon
text_template = <LDAP_NOTIFY_DIR>/templates/notify.tmpl.txt
html_template =
```

The rule options have the following meaning:

| Option  | Format   | Description | Examples |
|:------- |:-------- |:----------- |:---------|
| from_address | email address or empty | the from email address of a notification email | admin@company.com |
| from_text | string | the from text of a notification email | Password Notification |
| subject | string | the subject of a notification | expires in $days_left days
| text_template | absolute filename | the text template for notification emails | /etc/ldap-notify/notify-30.tmpl.txt |
| html_template | absolute filename | the html template for notification emails | /etc/ldap-notify/notify-30.tmpl.html |

The subject of the notification emails will be interpolated with the same variables as in the email template itself (cf. below).

## Templates ##

Email templates and email subjects for rules are interpolated with a number of variables. 

In the case of user notification emails:

| Variable  | Format | Description | Examples |
|:------- |:-------- |:----------- |:---------|
| expiry_date | string | the localized (according to the LANG setting) date of the expiration timestamp | 12.10.2014 for LANG=de_DE |
| days_left | integer | number of days from today to the expiration timestamp, rounded down | 4 |
| weeks_left | integer | number of weeks from today to the expiration timestamp, rounded down | 2 |
| months_left | integer | number of months from today to the expiration timestamp, roundded down | 1 |
| rule_days | integer | the days of the applying rule | 14 |
| cn | string | the common name of the user being notified | hschmidt |
| dn | DN | the DN of the user being notified | cn=hschmidt,ou=users,dc=localhost |
| fullname | string | the full name of the user being notified | Hans Schmidt |
