# =============================================================================
# Copyright [2014] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================


# This is an example application
# =============================================================================
import datetime
import os

import flask
import ewsgi
from cloudlib import parse_ini
from cloudlib import logger


CONFIG = parse_ini.ConfigurationSetup()

try:
    CONFIG.load_config(name='example', path=os.getcwd())

    # Load Default Configuration
    default_config = CONFIG.config_args(section='default')

    # Set the application name
    APPNAME = default_config.get('appname', 'example')

    # Store network Configuration
    network_config = CONFIG.config_args(section='network')

    # Store SSL configuration
    ssl_config = CONFIG.config_args(section='ssl')

    # Enable or disable DEBUG mode
    DEBUG = default_config.get('debug', False)
except IOError:
    # If the configuration file is not present, set the two bits we need
    DEBUG = True
    APPNAME = 'example'

# Load Logging
LOG = logger.getLogger(APPNAME)

# Load the flask APP
APP = flask.Flask(APPNAME)

# Enable general debugging
if DEBUG is True:
    APP.debug = True
    LOG.debug(APP.logger)

# Enable Application Threading
APP.threaded = True

# Enforce strict slashes in URI's
APP.url_map.strict_slashes = False

# Add Default Handling for File not found.
APP.errorhandler(ewsgi.not_found)

# Load the BLUEPRINT handler
BLUEPRINT = flask.Blueprint

blueprints = []


# Each Blueprint is essentially route. this has a name and needs to be
# stored as an object which will be used as a decorator.
hello_world = BLUEPRINT('hello', APPNAME)
test_path = BLUEPRINT('test_path', __name__)


# The decorator object is appended to the "blueprints" list and will be
# used later to register ALL blueprints.
blueprints.append(hello_world)
blueprints.append(test_path)


# This decorator loads the route and provides the allowed methods
# available from within the decorator
@hello_world.route('/hello', methods=['GET'])
def _hello_world():
    """Return 200 response on GET '/hello'."""
    LOG.debug('hello world')
    return 'hello world. The time is [ %s ]' % datetime.datetime.utcnow(), 200


@test_path.route('/test', methods=['GET'])
def _test_path():
    """Return 200 response on GET '/test'."""
    state = {
        'Application': APPNAME,
        'time': datetime.datetime.utcnow(),
        'request': {
            'method': flask.request.method,
            'path': flask.request.path
        }
    }
    LOG.debug(state)
    return flask.jsonify({'response': state}, indent=2), 200


# Register all blueprints as found in are `list` of blueprints
for blueprint in blueprints:
    APP.register_blueprint(blueprint=blueprint)
