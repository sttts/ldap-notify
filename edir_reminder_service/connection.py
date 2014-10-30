import sys
import os
import ldap
import os.path
import logging
log = logging.getLogger('edir-reminder-server')

# set timeouts to 10s
ldap.set_option(ldap.OPT_NETWORK_TIMEOUT, 10.0)
ldap.set_option(ldap.OPT_TIMEOUT, 10.0)

# connect to ldap
def connect_to_ldap(config):
    # configure TLS
    start_tls = False
    if config.server.startswith('ldaps:'):
        log.info("Demanding SSL trusted certificate")
        ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_DEMAND)
        start_tls = True
    
    log.info('Connecting to ' + config.server)
    con = ldap.initialize(config.server)
    
    if start_tls:
        log.info('Starting TLS')
        con.start_tls_s()
        
    #if config.LDAP_BIND_DN:
    #    log.info('Starting LDAP bind with ' + config.LDAP_BIND_DN)
    #    con.simple_bind_s(config.LDAP_BIND_DN, config.LDAP_BIND_PASSWORD)

    return con
