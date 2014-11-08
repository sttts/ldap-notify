from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import locale
import logging
log = logging.getLogger('edir_reminder_service.mail')
import smtplib
from string import Template

import edir_reminder_service.globals as g
from edir_reminder_service import ConfigError

class MailHandler(object):
    def __init__(self, config):
        self.config = config
        self.con = None
        self.templates = {}
        
    def smtp_connection(self):
        if self.con:
            return self.con
        
        if not self.config.smtp.server:
            raise ConfigError('No SMTP server defined')
        
        log.debug("Connecting to SMTP server '%s'" % self.config.smtp.server)
        if self.config.smtp.ssl:
            s = smtplib.SMTP_SSL(host=self.config.smtp.server, timeout=30)
        else:
            s = smtplib.SMTP(host=self.config.smtp.server, timeout=30)
        s.connect()
        s.ehlo()
        log.debug("Connected to SMTP server")
        if self.config.smtp.starttls:
            log.debug("Starting TLS")
            s.starttls()
        if self.config.smtp.user:
            log.debug("Authenticating with SMTP server")
            s.login(self.config.smtp.user, self.config.smtp.password)
        log.debug("SMTP connection established")
        self.con = s
        return self.con

    def close_con(self):
        if self.con:
            log.info("Closing Connection to SMTP Server")
            self.con.quit()
            self.con = None
        
    def __del__(self):
        self.close_con()
    
    def template(self, filename):
        if filename in self.templates:
            return self.templates[filename]
        
        f = open(filename, 'r')
        self.templates[filename] = Template(f.read())
        f.close()
        
        return self.templates[filename]

    def send_user_mail(self, rule, user, restricted=False):
        expiry_time = datetime.strptime(user.expiry, '%Y%m%d%H%M%SZ')
        template_env = {
            'expiry_date': expiry_time.date().strftime(locale.nl_langinfo(locale.D_FMT)),
            'days_left': str((expiry_time - g.NOW).days),
            'weeks_left': str((expiry_time - g.NOW).days / 7),
            'months_left': str((expiry_time - g.NOW).days / 30),
            'rule_days': str(rule.days),
            'cn': user.cn,
            'fullname': user.fullName if user.fullName else "Unknown User"
        }
        
        # send where?
        to = user.mail if not self.config.test.enabled else self.config.test.to_address
        
        # send what?
        if rule.html_template:
            html_msg = MIMEText(self.template(rule.html_template).substitute(template_env), 'html', 'utf-8')
        if rule.text_template:
            text_msg = MIMEText(self.template(rule.text_template).substitute(template_env), 'plain', 'utf-8')
        
        if rule.html_template and rule.text_template:
            msg = MIMEMultipart('alternative')
            msg.attach(html_msg)
            msg.attach(text_msg)
        elif rule.html_template:
            msg = html_msg
        elif rule.text_template:
            msg = text_msg
        else:
            raise ConfigError('Neither text_template nor html_template is defined for rule ' + str(rule.days))
            
        # setting mail headers
        msg['Subject'] = Template(rule.subject).substitute(template_env)
        msg['From'] = (rule.from_text + ' <' + rule.from_address +'>') if rule.from_text else rule.from_address
        msg['To'] = to
        
        # send message
        log.info('%sSending mail for %s to %s: %s' % ('RESTRICTED: ' if restricted else 'DRY: ' if self.config.dry else '', user.cn, to, msg['Subject']))
        if not restricted and not self.config.dry:
            try:
                smtp_con = self.smtp_connection()
                smtp_con.sendmail(rule.from_address, to, msg.as_string())
            except smtplib.SMTPException:
                self.close_con()
                raise
        
    def send_admin_report(self, config, notified_lines, failed_lines, without_email_lines, no_grace_logins_lines):
        # send where?
        to = config.admin.to_address if not self.config.test.enabled else self.config.test.to_address
        
        # send what
        template_env = {
            'notified_users': '\n'.join(notified_lines),
            'failed_users': '\n'.join(failed_lines),
            'users_without_email': '\n'.join(without_email_lines),
            'no_grace_logins': '\n'.join(no_grace_logins_lines),
            
            'notified_users_length': len(notified_lines),
            'failed_users_length': len(failed_lines),
            'users_without_email_length': len(without_email_lines),
            'no_grace_logins_length': len(no_grace_logins_lines),
        }
        admin_template = self.template(config.admin.text_template)
        msg = admin_template.substitute(template_env)
        
        # setting mail headers
        subject = Template(config.admin.subject).substitute(template_env)
        header = """Content-Type: text/plain; charset="utf-8"
Subject: %s
From: %s
To: %s

""" % (
    subject,
    (config.admin.from_text + '<' + config.admin.from_address +'>') if config.admin.from_text else config.admin.from_address,
    to
)

        # send message
        log.info('%sSending admin report to %s: %s' % ('DRY: ' if self.config.dry else '', to, subject))
        if self.config.dry:
            print
            print str(header+msg)
        else:
            try:
                smtp_con = self.smtp_connection()
                smtp_con.sendmail(config.admin.from_address, to, header+msg)
            except smtplib.SMTPException:
                self.close_con()
                raise