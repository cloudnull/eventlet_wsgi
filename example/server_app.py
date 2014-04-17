# Notes about using this example Flask Application.
#
# To use this EXAMPLE Flask Application I am assuming that you have NOT
# installed the eventlet_wsgi python application.  If you have installed the
# eventlet_wsgi python application comment out the following code snippet which
# allows you to execute the example application from within the example
# directory.
import os
import json
import sys


possible_topdir = os.path.normpath(
    os.path.join(
        os.path.abspath(
            sys.argv[0]
        ),
        os.pardir,
        os.pardir
    )
)
MAIN = os.path.join(possible_topdir, 'eventlet_wsgi', '__init__.py')


if os.path.exists(MAIN):
    sys.path.insert(0, possible_topdir)


# Example application
# =============================================================================

import datetime
import logging
import os

import flask

# Import the Server Run Method
import eventlet_wsgi
from eventlet_wsgi import run
from eventlet_wsgi.common import system_config


APPNAME = __name__
CONFIG = system_config.ConfigurationSetup()

# Load Default Configuration
default_config = CONFIG.config_args(section='default')

# Store network Configuration
network_config = CONFIG.config_args(section='network')

# Store SSL configuration
ssl_config = CONFIG.config_args(section='ssl')

# Load all of the relevant configuration bits
run.preload(loggers=[APPNAME])

# Load the flask APP
APP = flask.Flask(APPNAME)

# Set Debug Mode
DEBUG = default_config.get('debug', False)

# Load Logging
LOG = logging.getLogger(APPNAME)

# Enable general debugging
if DEBUG is True:
    APP.debug = True

# Enable Application Threading
APP.threaded = True

# Enforce strict slashes in URI's
APP.url_map.strict_slashes = False

# Add Default Handling for File not found.
APP.errorhandler(eventlet_wsgi.not_found)

# Load the BLUEPRINT handler
BLUEPRINT = flask.Blueprint

blueprints = []

# Each Blueprint is essentially route. this has a name and needs to be
# stored as an object which will be used as a decorator.
hello_world = flask.Blueprint('hello', APPNAME)

# The decorator object is appended to the "blueprints" list and will be
# used later to register all blueprints.
blueprints.append(hello_world)


# This decorator loads the route and provides the allowed methods
# available from within the decorator
@hello_world.route('/hello', methods=['GET'])
def _hello_world():
    """Return 200 response on GET '/hello'."""
    return 'hello world. The time is [ %s ]' % get_date(), 200


test_path = flask.Blueprint('test_path', __name__)
blueprints.append(test_path)


@test_path.route('/test', methods=['GET'])
def _test_path():
    """Return 200 response on GET '/test'."""
    state = {
        'Application': APPNAME,
        'time': get_date(),
        'request': {
            'method': flask.request.method,
            'path': flask.request.path
        }
    }
    return json.dumps({'response': state}), 200


def get_date():
    return datetime.datetime.utcnow()


# Run the new application
run.start_server(load_app=APP)
