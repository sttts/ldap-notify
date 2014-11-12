from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import locale
import logging
log = logging.getLogger('ldap_notify.mail')
import smtplib
from string import Template

import ldap_notify.globals as g
from ldap_notify import ConfigError

def capitalize(line):
    return ' '.join([s[0].upper() + s[1:] for s in line.split(' ')])

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
            s = smtplib.SMTP_SSL(timeout=10)
        else:
            s = smtplib.SMTP(timeout=10)
        if g.DEBUG > 3:
            s.set_debuglevel(True)
        s.connect(host=self.config.smtp.server)
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
            'dn': user.dn,
            'fullname': user.fullName if user.fullName else user.cn,
            'grace': str(user.loginGraceRemaining),
            
            'object': self.config.object,
            'objects': self.config.objects,
            'Object': capitalize(self.config.object),
            'Objects': capitalize(self.config.objects)
        }
        
        # send where?
        to = user.mail if (not self.config.test.enabled) or restricted or self.config.dry else self.config.test.to_address
        
        # send what?
        subject = Template(rule.subject).substitute(template_env)
        from_text = Template(rule.from_text).substitute(template_env) if rule.from_text else None
        verbose_from = (from_text + ' <' + rule.from_address +'>') if from_text else rule.from_address
        
        if rule.text_template:
            text = self.template(rule.text_template).substitute(template_env)
        if rule.html_template:
            # create mime body
            html_msg = MIMEText(self.template(rule.html_template).substitute(template_env), 'html', 'utf-8')
            if rule.text_template:
                text_msg = MIMEText(text, 'plain', 'utf-8')
                mime_msg = MIMEMultipart('alternative')
                mime_msg.attach(html_msg)
                mime_msg.attach(text_msg)
            else:
                mime_msg = html_msg

            # setting mime mail headers
            mime_msg['Subject'] = subject
            mime_msg['From'] = verbose_from
            mime_msg['To'] = to
            
            # convert to string
            msg = mime_msg.as_string()
        elif rule.text_template:
            header = """Content-Type: text/plain; charset="utf-8"
Subject: %s
From: %s
To: %s

""" % (
    subject,
    verbose_from,
    to
)
            msg = header + text
        else:
            raise ConfigError('Neither text_template nor html_template is defined for rule ' + str(rule.days))
        
        # send message
        log.info('%sSending mail for %s to %s: %s' % ('RESTRICTED: ' if restricted else 'DRY: ' if self.config.dry else '', user.cn, to, subject))
        if not restricted and not self.config.dry:
            try:
                smtp_con = self.smtp_connection()
                smtp_con.sendmail(rule.from_address, to, msg)
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

            'object': self.config.object,
            'objects': self.config.objects,
            'Object': capitalize(self.config.object),
            'Objects': capitalize(self.config.objects),
        }
        admin_template = self.template(config.admin.text_template)
        msg = admin_template.substitute(template_env)
        
        # setting mail headers
        subject = Template(config.admin.subject).substitute(template_env)
        from_text = Template(config.admin.from_text).substitute(template_env) if config.admin.from_text else None
        header = """Content-Type: text/plain; charset="utf-8"
Subject: %s
From: %s
To: %s

""" % (
    subject,
    (from_text + ' <' + config.admin.from_address +'>') if from_text else config.admin.from_address,
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
