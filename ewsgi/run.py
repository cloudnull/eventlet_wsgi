# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================
from ewsgi.server import wsgi

from cloudlib import logger
from cloudlib import parse_ini


def preload_and_start(app_name, load_app, config_path=None, config_ext='ini',
                      loggers=None):
    """Load all of our Configuration and logging before running the server.

    This will look for and use several sections from the configuration file
    loaded in the `app_name` configuration files.

    Built in sections loaded in configuration:
        * default - basic configuration for the server

        * network - network binds

        * ssl - ssl enabled or disabled

    The configuration file loaded can be change and or modified. `config_path`
    and `config_ext` are available to point the server to the known
    configuration file.

    :param app_name: ``str``
    :param load_app: ``object``
    :param config_path: ``str``
    :param config_ext: ``str``
    :param loggers: ``list``
    """

    if loggers is None:
        loggers = []

    config = parse_ini.ConfigurationSetup()
    config.load_config(name=app_name, path=config_path, ext=config_ext)

    default_config = config.config_args(section='default')
    network_config = config.config_args(section='network')
    ssl_config = config.config_args(section='ssl')

    loggers.append(default_config.get('appname', __name__))
    debug = default_config.get('debug', False)
    logging = logger.LogSetup(debug_logging=debug)

    for loggger in loggers:
        log = logging.default_logger(name=loggger)
        log.debug('Logger [ %s ] Running in Debug Mode' % loggger)

    start_server(
        load_app=load_app,
        default_cfg=default_config,
        network_cfg=network_config,
        ssl_cfg=ssl_config
    )


def start_server(load_app, default_cfg=None, network_cfg=None, ssl_cfg=None):
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
