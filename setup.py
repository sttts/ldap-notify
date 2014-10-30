#!/usr/bin/env python

from distutils.core import setup

setup(name='edir-reminder-service',
	description='eDirectory Login/Password Email Reminder Service',
    author='Dr. Stefan Schimanski',
    author_email='stefan.schimanski@gmail.com',
    url='https://github.com/sttts/edir-reminder-service',
    packages=['edir_reminder_service'],
    #data_files=[
    #	('/etc/edir-reminder-service', ['login.conf', 'password.conf']),
    #],
    package_data = {'edir_autoyast_ws': ['templates/*']},
    py_modules = ['edir_reminder_service_main']
)
