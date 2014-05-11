# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================
import errno
import os
import signal
import socket
import ssl
import time
import greenlet

import eventlet
from eventlet.green import ssl as wsgi_ssl
import eventlet.greenio
from eventlet import wsgi

from cloudlib import logger

import ewsgi


class Server(object):
    """Start an Eventlet WSGI server."""

    def __init__(self, load_app, app_name=__name__, default_cfg=None,
                 network_cfg=None, ssl_cfg=None, protocol='HTTP/1.1'):
        """Loads the flask application.

        :param load_app: ``object``
        :param app_name: ``str``
        :param default_cfg: ``dict``
        :param network_cfg: ``dict``
        :param ssl_cfg: ``dict``
        """
        # Set the app used within this WSGI server
        self.app = load_app
        self.app_name = app_name

        # Get configuration dictionaries
        self.net_cfg = self._empty_config(network_cfg)
        self.ssl_cfg = self._empty_config(ssl_cfg)
        self.def_cfg = self._empty_config(default_cfg)

        # Set the logger
        print self.def_cfg.get('appname', app_name)
        self.log = logger.getLogger(self.def_cfg.get('appname', app_name))

        self.debug = self.def_cfg.get('debug_mode', False)
        self.server_socket = self._socket_bind()

        wsgi.HttpProtocol.default_request_version = protocol
        self.protocol = wsgi.HttpProtocol

        pool_size = int(self.net_cfg.get('connection_pool', 1000))
        self.spawn_pool = eventlet.GreenPool(size=pool_size)

        self.active = True
        self.worker = None

        eventlet.patcher.monkey_patch()

    @staticmethod
    def _empty_config(config):
        """Return a configuration dict.

        :param config: ``dict``
        :return: ``dict``
        """
        if config is None:
            return {}
        else:
            return config

    def _ssl_kwargs(self):
        """Check if certificate files exist.

        When using SSL this will check to see if the keyfile, certfile
        and ca_certs exist on the system in the location provided by config.
        If a ca_cert is specified the ssl.CERT_REQUIRED will be set otherwise
        ssl.CERT_NONE is set.

        :return ssl_kwargs: ``dict``
        """
        ssl_kwargs = {'server_side': True}

        cert_files = ['keyfile', 'certfile', 'ca_certs']
        for cert_file in cert_files:
            cert = self.ssl_cfg.get(cert_file)
            if cert and not os.path.exists(cert):
                raise RuntimeError("Unable to find crt_file: %s" % cert)
            if cert:
                ssl_kwargs[cert_file] = cert

        if 'ca_certs' in ssl_kwargs:
            ssl_kwargs['cert_reqs'] = ssl.CERT_REQUIRED
        else:
            ssl_kwargs['cert_reqs'] = ssl.CERT_NONE

        return ssl_kwargs

    def _socket_bind(self):
        """Bind to socket on a host.

        From network config bind_host and bind_port will be used as the socket
        the WSGI server will be bound too. The method will attempt to bind to
        the socket for 30 seconds. If the socket is unusable after 30 seconds
        an exception is raised.

        :return sock: ``object``
        """
        tcp_listener = (
            str(self.net_cfg.get('bind_host', '127.0.0.1')),
            int(self.net_cfg.get('bind_port', 8080))
        )
        self.log.debug(tcp_listener)

        wsgi_backlog = self.net_cfg.get('backlog', 128)
        if wsgi_backlog < 1:
            raise SystemExit('the backlog value must be >= 1')

        sock = None
        retry_until = time.time() + 30
        while not sock and time.time() < retry_until:
            try:
                sock = eventlet.listen(
                    tcp_listener,
                    family=socket.AF_INET,
                    backlog=wsgi_backlog
                )

                if self.ssl_cfg.get('use_ssl', False) is True:
                    sock = wsgi_ssl.wrap_socket(
                        sock, **self._ssl_kwargs()
                    )

            except socket.error as err:
                if err.args[0] != errno.EADDRINUSE:
                    raise ewsgi.WSGIServerFailure(
                        'Not able to bind to socket %s %s' % tcp_listener
                    )
                retry_time_left = retry_until - time.time()
                self.log.warn(
                    'Waiting for socket to become available... Time available'
                    ' for retry %s', int(retry_time_left)
                )
                eventlet.sleep(1)
            else:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                return sock
        else:
            raise ewsgi.WSGIServerFailure('Socket Bind Failure.')

    def _start(self):
        """Start the WSGI server."""
        wsgi.server(
            self.server_socket,
            self.app,
            custom_pool=self.spawn_pool,
            protocol=self.protocol,
            log=ewsgi.EventLogger(self.log),
        )
        self.spawn_pool.waitall()

    def start(self):
        """Start the WSGI Server worker."""
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGHUP, self.stop)
        self.worker = eventlet.spawn(self._start)
        self.log.info('%s Has started.' % self.app_name)

    def stop(self, *args):
        """Stop the WSGI server.

        :param args: ``list``
        """
        self.log.warn('Stopping [ %s ] server.' % self.app_name)
        self.log.debug(args)
        if self.worker is not None:
            # Resize pool to stop new requests from being processed
            self.spawn_pool.resize(0)
            self.worker.kill()

    def wait(self):
        """Block, until the server has stopped."""
        try:
            if self.worker is not None:
                self.worker.wait()
        except greenlet.GreenletExit:
            self.log.warn('[ %s ] ewsgi server has stopped.' % self.app_name)
            self.stop(self)
        except OSError as exp:
            self.log.fatal(
                '[ %s ] ewsgi server has been halted, Reason [ %s ].',
                self.app_name, exp
            )
            self.stop(self)
