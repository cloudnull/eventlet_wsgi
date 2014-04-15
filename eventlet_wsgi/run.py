# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================
from eventlet_wsgi import info
from eventlet_wsgi.api import wsgi
from eventlet_wsgi.common import logger, system_config


CONFIG = system_config.ConfigurationSetup()


def preload():
    """Load all of our Configuration and logging before running the server."""

    default_config = CONFIG.config_args()
    if 'appname' in default_config:
        info.__appname__ = default_config['appname']

    debug = default_config.get('debug', False)
    log = logger.logger_setup(name=info.__appname__, debug_logging=debug)
    log.debug('System Running in Debug Mode')


def start_server(load_app=None):
    """Start the WSGI Server."""
    wsgi_server = wsgi.Server(load_app=load_app)
    wsgi_server.start()
    wsgi_server.wait()


def executable():
    """Run the default server."""
    preload()
    start_server()


if __name__ == '__main__':
    executable()
