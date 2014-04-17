# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================
import json


def not_found(message=None, error=None):
    """Return Message when an API request is not found.

    :param message: ``str``
    :param error: ``int``
    :return json, status: ``tuple``
    """
    if message is None:
        message = "resource not found"

    if error is None:
        error = 404

    return json.dumps({"response": message}), error


class WSGIServerFailure(Exception):
    """Exception when WSGI application can not start."""
    pass


class CantContinue(Exception):
    """Exception when the application stack can not continue."""
    pass


class ProcessFailure(Exception):
    """Exception when the application stack has a process failure."""
    pass


class EventLogger(object):
    """Respond to the write command using a logger.

    :param logger: ``func``
    :param level: ``str``
    """
    def __init__(self, logger, level='debug'):
        self.logger = logger
        self.level = level

    def write(self, msg):
        log = getattr(self.logger, self.level)
        log(msg.strip("\n"))
