# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================
import argparse
import ConfigParser
import os
import stat
import sys

from eventlet_wsgi import info


def is_int(value):
    """Return int if the value can be an int.

    :param value: ``str``
    :return: ``int`` :return: ``str``
    """
    try:
        return int(value)
    except ValueError:
        return value


class ConfigurationSetup(object):
    """Parse arguments from a Configuration file.

    Note that anything can be set as a "Section" in the argument file.
    """
    def __init__(self):
        name = info.__appname__
        self.args = self._arguments()

        if self.args.config_file is None:
            self.config_file = os.path.join('/etc/', name, '%s.conf' % name)
        else:
            self.config_file = self.args.config_file

    @staticmethod
    def _arguments():
        """Setup argument Parsing."""

        name = info.__appname__
        parser = argparse.ArgumentParser(
            usage='%(prog)s',
            description='Eventlet WSGI Server',
            epilog='Licensed "GPLv3"')

        parser.add_argument(
            '--debug',
            help='Enable Debug mode, Default %(default)s',
            action='store_true',
            default=False
        )

        parser.add_argument(
            '--config-file',
            help='Set the path to the configuration file, Default %(default)s',
            metavar='',
            default=os.path.join('/etc/', name, '%s.conf' % name)
        )
        return parser.parse_args()

    def _set_cli_args(self, args, section):
        if section == 'default':
            args.update(vars(self.args))
            return args
        else:
            return args

    def config_args(self, section='default'):
        """Loop through the configuration file and set all of our values.

        :param section: ``str``
        :return: ``dict``
        """
        args = {}
        # setup the parser to for safe config parsing with a no value argument
        # Added per - https://github.com/cloudnull/turbolift/issues/2
        if sys.version_info >= (2, 7, 0):
            parser = ConfigParser.SafeConfigParser(allow_no_value=True)
        else:
            parser = ConfigParser.SafeConfigParser()

        # Set to preserve Case
        parser.optionxform = str

        try:
            parser.read(self.config_file)
            for name, value in parser.items(section):
                name = name.encode('utf8')
                if any([value == 'False', value == 'false']):
                    value = False
                elif any([value == 'True', value == 'true']):
                    value = True
                else:
                    value = is_int(value=value)
                args[name] = value
        except Exception:
            return self._set_cli_args(args, section)
        else:
            return self._set_cli_args(args, section)
