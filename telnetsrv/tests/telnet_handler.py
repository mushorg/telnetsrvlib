from gevent import monkey; monkey.patch_all()
import logging
import gevent
import curses
from curses import ascii
from gevent import server
from telnetsrv.green import TelnetHandler, command
from telnetsrv.utils import bytes_to_str
logging.getLogger('').setLevel(logging.DEBUG)


# The TelnetHandler instance is re-created for each connection.
# Therfore, in order to store data between connections, create
# a seperate object to deal with any logic that needs to persist
# after the user logs off.
# Here is a simple example that just counts the number of connections
# as well as the number of times this user has connected.

class MyServer(object):
    """A simple server class that just keeps track of a connection count."""
    def __init__(self):
        # Var to track the total connections.
        self.connection_count = 0

        # Dictionary to track individual connections.
        self.user_connect = {}

    def new_connection(self, username):
        """Register a new connection by username, return the count of connections."""
        self.connection_count += 1
        try:
            self.user_connect[username] += 1
        except:
            self.user_connect[username] = 1
        return self.connection_count, self.user_connect[username]


# Subclass TelnetHandler to add our own commands and to call back
# to myserver.


class DummyTelnetHandler(TelnetHandler):
    # Create the instance of the server within the class for easy use
    myserver = MyServer()

    # -- Override items to customize the server --

    WELCOME = b'You have connected to the test server.'
    PROMPT = b"TestServer> "
    authNeedUser = True
    authNeedPass = False

    def authCallback(self, username, password):
        """Called to validate the username/password."""
        # Note that this method will be ignored if the SSH server is invoked.
        # We accept everyone here, as long as any name is given!
        if not username:
            # complain by raising any exception
            raise AssertionError

    def session_start(self):
        """Called after the user successfully logs in."""
        self.writeline(b'This server is running.')

        # Tell myserver that we have a new connection, and provide the username.
        # We get back the login count information.
        globalcount, usercount = self.myserver.new_connection( self.username )

        self.writeline(b'Hello %s!' % self.username)
        self.writeline(b'You are connection #%a, you have logged in %a time(s).' % (globalcount, usercount))

    def session_end(self):
        """Called after the user logs off."""

        # Cancel any pending timer events.  Done a bit different between Greenlets and threads
        for event in self.timer_events:
            event.kill()

    def writeerror(self, text):
        """Called to write any error information (like a mistyped command).
        Add a splash of color using ANSI to render the error text in red.
        see http://en.wikipedia.org/wiki/ANSI_escape_code"""
        TelnetHandler.writeerror(self, "\x1b[91m%s\x1b[0m" % text )

    # -- Custom Commands --
    @command('debug')
    def command_debug(self, params):
        """
        Display some debugging data
        """
        for (v, k) in list(self.ESCSEQ.items()):
            line = '%-10s : ' % (self.KEYS[k], )
            for c in v:
                if ord(c) < 32 or ord(c) > 126:
                    line = line + curses.ascii.unctrl(c)
                else:
                    line = line + c
            self.writeresponse(line)

    @command('params')
    def command_params(self, params):
        """[<params>]*
        Echos back the raw received parameters.
        """
        self.writeresponse(b"params == %r" % params)

    @command('info')
    def command_info(self, params):
        """
        Provides some information about the current terminal.
        """
        self.writeresponse(b"Username: %a, terminal type: %a" % (bytes_to_str(self.username), self.TERM))
        self.writeresponse(b"Command history:")
        for c in self.history:
            self.writeresponse("  %r" % bytes_to_str(c))

    @command(['timer', 'timeit'])
    def command_timer(self, params):
        """<time> <message>
        In <time> seconds, display <message>.
        Send a message after a delay.
        <time> is in seconds.
        If <message> is more than one word, quotes are required.

        example: TIMER 5 "hello world!"
        """
        try:
            timestr, message = params[:2]
            delay = int(timestr)
        except ValueError:
            self.writeerror(b"Need both a time and a message" )
            return
        self.writeresponse(b"Waiting %d seconds..." % delay)

        event = gevent.spawn_later(delay, self.writemessage, message)
        # Used by session_end to stop all timer events when the user logs off.
        self.timer_events.append(event)

    @command('passwd')
    def command_set_password(self, params):
        """[<password>]
        Pretends to set a console password.
        Pretends to set a console password.
        Demonostrates how sensative information may be handled
        """
        try:
            password = params[0]
        except:
            password = self.readline(prompt=b"New Password: ", echo=False, use_history=False)
        else:
            # If the password was a parameter, it will have been stored in the history.
            # snip it out to prevent easy snooping
            self.history[-1] = 'passwd'

        password2 = self.readline(prompt=b"Retype New Password: ", echo=False, use_history=False)
        if password == password2:
            self.writeresponse(b'Pretending to set new password, but not really.')
        else:
            self.writeerror(b'Passwords don\'t match.')

    # Older method of defining a command
    # must start with "cmd" and end wtih the command name.
    # Aliases may be attached after the method definitions.
    def cmdECHO(self, params):
        """<text to echo>
        Echo text back to the console.

        """
        self.writeresponse( ' '.join(params) )
    # Create an alias for this command
    cmdECHO.aliases = ['REPEAT']

    def cmdTERM(self, params):
        """
        Hidden command to print the current TERM

        """
        self.writeresponse(self.TERM)
    # Hide this command, old-style syntax.  Will not show in the help list.
    cmdTERM.hidden = True

    @command('hide-me', hidden=True)
    @command(['hide-me-too', 'also-me'])
    def command_do_nothing(self, params):
        """
        Hidden command to perform no action

        """
        self.writeresponse('Nope, did nothing.')


if __name__ == '__main__':
    TELNET_IP_BINDING = '127.0.0.1' # all
    TELNET_PORT_BINDING = 7777
    Handler = DummyTelnetHandler
    server = gevent.server.StreamServer((TELNET_IP_BINDING, TELNET_PORT_BINDING), Handler.streamserver_handle)
    logging.info("Starting Telnet server at {}.  (Ctrl-C to stop)".format((TELNET_IP_BINDING, TELNET_PORT_BINDING)))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logging.info("Server shut down.")

