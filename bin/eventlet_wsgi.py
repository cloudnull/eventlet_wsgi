#!/usr/bin/env python
# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================

import os
import sys


possible_topdir = os.path.normpath(
    os.path.join(
        os.path.abspath(
            sys.argv[0]
        ),
        os.pardir,
        os.pardir
    )
)


MAIN = os.path.join(possible_topdir, 'eventlet_wsgi', '__init__.py')


if os.path.exists(MAIN):
    sys.path.insert(0, possible_topdir)


from eventlet_wsgi import run
run.executable()
