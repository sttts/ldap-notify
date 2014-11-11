#!/usr/bin/env python

from setuptools import setup

setup(name='ldap-notify',
	description='LDAP Login/Password Email Notification Service',
	version='0.9.0',
	long_description="""\
      `ldap-notify` searches users in an LDAP directory whose login or password expires in a certain number of days. These users are notified with a customizable email. The time intervals for the notifications and the email templates can be freely defined. By using a custom LDAP attribute the last notification is stored in the directory such that users are only notified once per rule. Moreover, this mechanism allows running the tool (e.g. via cron) on multiple machine with a certain time delta in order to implement high availabiliy. 
      """,
    author='Dr. Stefan Schimanski',
    author_email='stefan.schimanski@gmail.com',
    url='https://github.com/sttts/ldap_notify',
    packages=['ldap_notify'],
    package_data = {'ldap_notify': ['templates/*']},
    scripts=[ 'scripts/ldap-notify' ],
	classifiers=[
		"License :: OSI Approved :: GNU General Public License (GPL)",
	  	"Programming Language :: Python",
	  	"Development Status :: 4 - Beta",
	  	"Topic :: System :: Systems Administration :: Authentication/Directory :: LDAP"
	],
	keywords='ldap notification eDirectory',
	license='GPL',
	install_requires=[
		'python-ldap',
	]
)
