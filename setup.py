#!/usr/bin/env python

from distutils.core import setup

setup(name='edir-reminder-service',
	description='eDirectory Login/Password Email Reminder Service',
    author='Dr. Stefan Schimanski',
    author_email='stefan.schimanski@gmail.com',
    url='https://github.com/sttts/edir-reminder-service',
    packages=['ldap_notify'],
    #data_files=[
    #	('/etc/edir-reminder-service', ['login.conf', 'password.conf']),
    #],
    package_data = {'edir_autoyast_ws': ['templates/*']},
    py_modules = ['ldap_notify_main']
)
