# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================
from eventlet_wsgi.server import wsgi
from eventlet_wsgi.common import logger
from eventlet_wsgi.common import system_config


CONFIG = system_config.ConfigurationSetup()


def preload(loggers=None):
    """Load all of our Configuration and logging before running the server.

    :param loggers: ``list``
    """

    if loggers is None:
        loggers = []

    default_config = CONFIG.config_args(section='default')
    loggers.append(default_config.get('appname', __name__))
    debug = default_config.get('debug', False)

    for loggger in loggers:
        log = logger.logger_setup(name=loggger, debug_logging=debug)
        log.debug('Logger [ %s ] Running in Debug Mode' % loggger)


def start_server(load_app=None, default_cfg=None, network_cfg=None,
                 ssl_cfg=None):
    """Start the WSGI Server.

    :param load_app: ``object``
    :param default_cfg: ``dict``
    :param network_cfg: ``dict``
    :param ssl_cfg: ``dict``
    """
    wsgi_server = wsgi.Server(
        load_app=load_app,
        default_cfg=default_cfg,
        network_cfg=network_cfg,
        ssl_cfg=ssl_cfg
    )
    wsgi_server.start()
    wsgi_server.wait()


def executable():
    """Run the default server."""
    preload()
    start_server()


if __name__ == '__main__':
    executable()
