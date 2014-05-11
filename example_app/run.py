# =============================================================================
# Copyright [2014] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================

# Notes about using this example Flask Application.
#
# To use this EXAMPLE Flask Application I am assuming that you have NOT
# installed the ewsgi python application.  If you have installed the
# ewsgi python application comment out the following code snippet which
# allows you to execute the example_app application from within the example_app
# directory.
import sys
import os


possible_topdir = os.path.normpath(
    os.path.join(
        os.path.abspath(
            sys.argv[0]
        ),
        os.pardir,
        os.pardir
    )
)
MAIN = os.path.join(possible_topdir, 'ewsgi', '__init__.py')


if os.path.exists(MAIN):
    sys.path.insert(0, possible_topdir)


# Now take the built app and run it via the ewsgi server, nice and simple!
# =============================================================================
from ewsgi import run
import app

# Run the new application
# Load all of the relevant configuration bits
run.preload_and_start(
    app_name=app.APPNAME,
    load_app=app.APP,
    config_path=os.getcwd(),
    loggers=[app.APPNAME]
)
