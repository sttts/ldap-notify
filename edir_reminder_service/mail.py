from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging
log = logging.getLogger('edir_reminder_service.mail')
from smtplib import SMTP, SMTP_SSL, SMTPException

import edir_reminder_service.globals as g
from edir_reminder_service import ConfigError

class MailHandler(object):
	def __init__(self, config):
		self.config = config
		self.s = None
		
	def smtp_connection(self):
		if self.s:
			return self.s
		
		if not self.config.smtp.server:
			raise ConfigError('No SMTP server defined')
		
		log.debug("Connecting to SMTP server '%s'" % self.config.smtp.server)
		try:
			if self.config.smtp.ssl:
				s = SMTP_SSL(host=self.config.smtp.server, timeout=30)
			else:
				s = SMTP(host=self.config.smtp.server, timeout=30)
			s.connect()
			s.ehlo()
			log.debug("Connected to SMTP server")
			if self.config.smtp.tls:
				log.debug("Starting TLS")
				s.starttls()
			if self.config.smtp.user:
				log.debug("Authenticating with SMTP server")
				s.login(self.config.smtp.user, self.config.smtp.password)
			log.debug("SMTP connection established")
			self.s = s
		except SMTPException:
			raise

	def __del__(self):
		if self.s:
			log.info("Closing Connection to SMTP Server")
			self.s.quit()

	def send_user_mail(self, rule, user, alternative_to=None):
		expiry_time = datetime.strptime(user.expiry, '%Y%m%d%H%M%SZ')
		days_left = (expiry_time - g.NOW).days
		
		# send where?
		if not self.config.test.test:
			to = alternative_to or user.mail
		else:
			to = self.config.test.to_address
		
		# send what?
		if rule.html_template:
			html_msg = MIMEText(rule.html_template, 'html', 'utf-8')
		if rule.text_template:
			text_msg = MIMEText(rule.text_template, 'plain', 'utf-8')
		
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
		msg['Subject'] = rule.subject
		msg['From'] = (rule.from_text + '<' + rule.from_address +'>') if rule.from_text else rule.from_address
		msg['To'] = to
		
		# send message
		log.info('%sSending mail for %s to %s: %s' % ('DRY: ' if self.config.test.dry else 'TEST:' if self.config.test.test else '',
													  user.cn, to, msg['Subject']))
		if not self.config.test.dry:
			smtp_con = self.smtp_connection()
			raise Exception('tried to send') #self.s.sendmail(rule.from_address, to, msg.as_string())
