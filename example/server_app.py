# Notes about using this example Flask Application.
#
# To use this EXAMPLE Flask Application I am assuming that you have NOT
# installed the eventlet_wsgi python application.  If you have installed the
# eventlet_wsgi python application comment out the following code snippet which
# allows you to execute the example application from within the example
# directory.
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



# Example application
# =============================================================================

# Import the MainApplication Class which will be subclassed
from eventlet_wsgi.api.application import MainApplication


# Import the Server Run Method
from eventlet_wsgi import run


# Load all of the relevant configuration bits
run.preload()


class AppClass(MainApplication):
    """This is a subclass of the Main Application class.

    This allows you to create a custom Flask Application without having to
    setup and or dealing with a server.
    """
    def __init__(self):
        super(AppClass, self).__init__()
        self.blueprints = []

    def get_date(self):
        import datetime
        return datetime.datetime.utcnow()

    def routes(self):
        """Load our new application routes.

        To create a route do the following:
        >>> newbp = flask.Blueprint('newbp', __name__)
        >>> @newbp('/some/path', methods=['GET'])
        >>> def _newbp():
        ...    return self.flask.jsonify({'response': 'somedata'}), 200
        >>> self.app.register_blueprint(newbp)
        """
        # Each Blueprint is essentially route. this has a name and needs to be
        # stored as an object which will be used as a decorator.
        hello_world = self.blueprint('hello', __name__)

        # The decorator object is appended to the "blueprints" list and will be
        # used later to register all blueprints.
        self.blueprints.append(hello_world)

        # This decorator loads the route and provides the allowed methods
        # available from within the decorator
        @hello_world.route('/hello', methods=['GET'])
        def _hello_world():
            """Return 200 response on GET '/hello'."""
            self.log.debug(self.flask.request.method)
            return 'hello world. The time is [ %s ]' % self.get_date(), 200

        test_path = self.blueprint('test_path', __name__)
        self.blueprints.append(test_path)

        @test_path.route('/test', methods=['GET'])
        def _test_path():
            """Return 200 response on GET '/test'."""
            state = {
                'Application': self.name,
                'time': self.get_date(),
                'request': {
                    'method': self.flask.request.method,
                    'path': self.flask.request.path
                }
            }
            self.log.debug(str(state))
            return self.flask.jsonify({'response': state}), 200


# Run the new application with the subclass'd MainApplication
run.start_server(load_app=AppClass())
