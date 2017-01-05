import logging
import os

def get_from_environment(variable, default):
    if variable in os.environ:
        v = os.environ.get(variable)
        logging.info("Using environment variable %s=%s" % (variable, default))
    else:
        v = default
        logging.warning("Using default variable %s=%s" % (variable, default))
    return v

