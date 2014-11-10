#!/usr/bin/env python

from distutils.core import setup
import distutils.sysconfig

setup(name='ldap_notify',
	description='LDAP Login/Password Email Notification Service',
    author='Dr. Stefan Schimanski',
    author_email='stefan.schimanski@gmail.com',
    url='https://github.com/sttts/ldap_notify',
    packages=['ldap_notify'],
    data_files=[
    	('/etc/ldap-notify', ['conf/login.conf', 'conf/password.conf']),
    ],
    package_data = {'ldap-notify': ['templates/*']},
    scripts = [ 'scripts/ldap-notify' ]
)
