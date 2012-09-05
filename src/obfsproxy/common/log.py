# obfsproxy logging code

import logging

# XXX Add Formatter!!!

our_logger = logging.getLogger('our_logger')
our_logger.propagate = False

def set_log_file(filename):
    log_handler = logging.FileHandler(filename)
    our_logger.addHandler(log_handler)

def set_log_severity(sev_string):
    numeric_level = getattr(logging, sev_string.upper(), None)
    our_logger.setLevel(numeric_level)

def disable_logs():
    logging.disable(logging.CRITICAL)

# Redirect logging functions to our custom logger.
debug = our_logger.debug
info = our_logger.info
warning = our_logger.warning
error = our_logger.error
critical = our_logger.critical
