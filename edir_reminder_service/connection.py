import ldap
import logging
log = logging.getLogger('edir-reminder-server')

# set timeouts to 10s
ldap.set_option(ldap.OPT_NETWORK_TIMEOUT, 10.0)
ldap.set_option(ldap.OPT_TIMEOUT, 10.0)

# connect to ldap
def connect_to_ldap(config):
    # configure TLS
    start_tls = False
    if config.server.startswith('ldaps:') or config.start_tls:
        log.info("Using SSL/TLS")
        ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_DEMAND)
        start_tls = True
    
    if config.ignore_cert:
        log.info("Ignoring SSL/TLS certificate")
        ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_ALLOW)
    
    log.info('Connecting to ' + config.server)
    con = ldap.initialize(config.server)
    
    if start_tls:
        log.info('Starting TLS')
        con.start_tls_s()
    
    if config.bind_dn:
        log.info('Starting LDAP bind with ' + config.bind_dn)
        con.simple_bind_s(config.bind_dn, config.bind_password)

    return con
