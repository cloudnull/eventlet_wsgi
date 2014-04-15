# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================
import logging
import os

import flask
import flask_sqlalchemy

import eventlet_wsgi

from eventlet_wsgi import info
from eventlet_wsgi.common import system_config

# Load the configuration files
CONFIG = system_config.ConfigurationSetup()

# Load Default Configuration
default_config = CONFIG.config_args()

# Set Debug Mode
DEBUG = default_config.get('debug', False)

# Set the application name
if 'appname' in default_config:
    APPNAME = default_config['appname']
else:
    APPNAME = default_config['appname'] = info.__appname__

# Load Logging
LOG = logging.getLogger(APPNAME)

# Load the flask APP
APP = flask.Flask(APPNAME)

# Store Default Configuration
APP.config['default'] = default_config

# Store network Configuration
APP.config['network'] = CONFIG.config_args(section='network')

# Store SSL configuration
APP.config['ssl'] = CONFIG.config_args(section='ssl')

# Store SQL Configuration
sql_config = APP.config['sql'] = CONFIG.config_args(section='sql')

# Load NewRelic plugin if found
NEWRELIC = default_config.get('newrelic')
try:
    if NEWRELIC and os.path.exists(NEWRELIC):
        import newrelic.agent
        newrelic.agent.initialize(NEWRELIC)
        LOG.info('Newrelic Plugin Loaded')
except ImportError as exp:
    LOG.error('[ %s ] was not importable, is it installed?' % exp)

# Enable general debugging
if DEBUG is True:
    APP.debug = True

# Load FLASK SQL Alchemy
if sql_config:
    sql_connection = default_config.get('sql_connection')
    if sql_connection is not None:
        if DEBUG is True:
            APP.config['SQLALCHEMY_ECHO'] = True

        APP.config['SQLALCHEMY_DATABASE_URI'] = sql_connection
        APP.config['SQLALCHEMY_POOL_SIZE'] = int(
            sql_config.get('pool_size', 250)
        )
        APP.config['SQLALCHEMY_POOL_TIMEOUT'] = sql_config.get(
            'pool_timeout', 60
        )
        APP.config['SQLALCHEMY_POOL_RECYCLE'] = sql_config.get(
            'pool_recycle', 120
        )

        DB = flask_sqlalchemy.SQLAlchemy(APP)
        DB.init_app(APP)


class MainApplication(object):
    def __init__(self):
        """Load the Flask Application.

        To use this module you have several options.  One would be to use the
        subclass the Application class and overload the "return_app" method.
        You could also simply import the APP constant build your application
        outside the scope of this class.

        This is the main Load point used in the WSGI server.

        Presets are:
            app.Threaded = True
            app.url_map.strict_slashes = False
            app.errorhandler(eventlet_wsgi.not_found)

        self.blueprint = is available to build out new blueprints
        self.flask     = is available to provide in class flask capabilities
                         without re-importing.
        self.log       = Pre loaded Logger
        self.name      = Name of the application
        """

        # Load Flask APP
        self.app = APP

        # Load a logger
        self.log = LOG

        # Application Name
        self.name = APPNAME

        # Enable Application Threading
        self.app.threaded = True

        # Enforce strict slashes in URI's
        self.app.url_map.strict_slashes = False

        # Add Default Handling for File not found.
        self.app.errorhandler(eventlet_wsgi.not_found)

        # Load the blueprint handler
        self.blueprint = flask.Blueprint

        # Load flask capabilities
        self.flask = flask

        # create an empty list where all application blueprints are stored
        self.blueprints = []

    def routes(self):
        """Load a routes for the Flask Application.

        The load method should only be called when the "application" module has
        already been imported by the "WSGI" server.

        The basic flask application is using blueprints. To use blueprints
        please build off of the following example.

        >>> newbp = flask.Blueprint('newbp', __name__)
        >>> @newbp('/some/path', methods=['GET'])
        >>> def _newbp():
        ...    return self.flask.jsonify({'response': 'somedata'}), 200
        >>> APP.register_blueprint(newbp)

        Notice that this is set to allow you to instantiate a new blueprint
        with a set function and decorator which can execute other methods,
        imports, or code.
        """

        general = self.blueprint('general', __name__)

        @general.route('/', methods=['GET'])
        def _general():
            """Return 200 response on GET '/'

            :return json, status: tuple
            """
            state = {
                'Application': self.name,
                'request': {
                    'method': self.flask.request.method,
                    'path': self.flask.request.path
                }
            }
            self.log.debug(str(state))
            return self.flask.jsonify({'response': state}), 200

        APP.register_blueprint(general)

    def register_blueprints(self):
        """Register all known Blueprints."""
        if not self.blueprints:
            raise eventlet_wsgi.CantContinue('No Blueprints to Register')

        for blueprint in self.blueprints:
            self.app.register_blueprint(blueprint)

    def return_app(self):
        r"""Load in the application and routes.

        :return APP: ``class`` # Loaded Flask API application
        """

        self.routes()
        self.register_blueprints()
        return APP
