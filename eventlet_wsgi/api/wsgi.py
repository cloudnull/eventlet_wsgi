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
import logging
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

import eventlet_wsgi
from eventlet_wsgi import info


class Server(object):
    """Start an Eventlet WSGI server."""
    def __init__(self, load_app=None):
        """Loads the flask application."""

        # load the application class
        if load_app is None:
            from eventlet_wsgi.api import application
            app = application.MainApplication()
        else:
            app = load_app

        # Set the app used within this WSGI server
        self.app = app.return_app()

        self.net_cfg = self.app.config.get('network', {})
        self.ssl_cfg = self.app.config.get('ssl', {})
        self.def_cfg = self.app.config.get('default', {})

        # Set the logger
        self.log = logging.getLogger(self.def_cfg.get('appname'))

        self.debug = self.def_cfg.get('debug_mode', False)
        self.server_socket = self._socket_bind()

        wsgi.HttpProtocol.default_request_version = "HTTP/1.0"
        self.protocol = wsgi.HttpProtocol

        pool_size = int(self.net_cfg.get('connection_pool', 1000))
        self.spawn_pool = eventlet.GreenPool(size=pool_size)

        self.active = True
        self.worker = None

        eventlet.patcher.monkey_patch()

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

        wsgi_backlog = self.net_cfg.get('backlog', 128)
        if wsgi_backlog < 1:
            raise SystemExit('the backlog value must be >= 1')

        sock = None
        retry_until = time.time() + 30
        while not sock and time.time() < retry_until:
            try:
                sock = eventlet.listen(
                    tcp_listener,
                    backlog=wsgi_backlog,
                    family=socket.AF_INET
                )

                if self.ssl_cfg.get('use_ssl', False) is True:
                    sock = wsgi_ssl.wrap_socket(
                        sock, **self._ssl_kwargs()
                    )

            except socket.error as err:
                if err.args[0] != errno.EADDRINUSE:
                    raise eventlet_wsgi.WSGIServerFailure(
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
            raise eventlet_wsgi.WSGIServerFailure('Socket Bind Failure.')

    def _start(self):
        """Start the WSGI server."""
        wsgi.server(
            self.server_socket,
            self.app,
            custom_pool=self.spawn_pool,
            protocol=self.protocol,
            log=eventlet_wsgi.EventLogger(self.log),
        )
        self.spawn_pool.waitall()

    def start(self):
        """Start the WSGI Server worker."""
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGHUP, self.stop)
        self.worker = eventlet.spawn(self._start)
        self.log.info('%s Has started.' % info.__appname__)

    def stop(self, *args):
        """Stop the WSGI server.

        :param args: ``list``
        """
        self.log.warn('Stopping [ %s ] server.' % info.__appname__)
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
            self.log.warn("[ %s ] WSGI server has stopped." % info.__appname__)
