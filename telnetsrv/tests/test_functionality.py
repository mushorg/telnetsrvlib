import unittest
import gevent
from gevent import server, socket
from telnetsrv.tests.telnet_handler import DummyTelnetHandler


class TestTelnetServer(unittest.TestCase):
    def setUp(self):
        self.Handler = DummyTelnetHandler
        self.server = gevent.server.StreamServer(('127.0.0.1', 0), self.Handler.streamserver_handle)
        self.server_greenlet = gevent.spawn(self.server.serve_forever)
        gevent.sleep(1)

    def tearDown(self):
        self.server.stop(timeout=5)
        gevent.joinall([self.server_greenlet])

    def test_auth_banner_welcome(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('127.0.0.1', self.server.server_port))
        _ = s.recv(2048)
        s.send(b'test_user\r\n')
        _ = s.recv(1024)
        s.send(b'\r\n')
        data = s.recv(1024)
        s.close()
        self.assertIn(b'This server is running.\r\nHello test_user!', data)

    def test_cmd_echo(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('127.0.0.1', self.server.server_port))
        _ = s.recv(2048)
        s.sendall(b'test_user\r\n')
        _ = s.recv(1024)
        s.sendall(b'\r\n')
        _ = s.recv(1024)
        s.sendall(b'echo Hi! This is a test!\r\n')
        _ = s.recv(1024)
        s.sendall(b'\r\n')
        data = s.recv(1024)
        s.close()
        self.assertEqual(data, b'TestServer> echo Hi! This is a test!\r\nHi! This is a test!\r\nTestServer> ')

    def test_cmd_help(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('127.0.0.1', self.server.server_port))
        _ = s.recv(2048)
        s.sendall(b'test_user\r\n')
        _ = s.recv(1024)
        s.sendall(b'\r\n')
        _ = s.recv(1024)
        s.sendall(b'?\r\n')
        _ = s.recv(1024)
        s.sendall(b'\r\n')
        data = s.recv(1024)
        s.close()
        self.assertIn(b'TestServer> ?\r\nHelp on built in commands\r\n\r\n? [<command>] - '
                      b'Display help\r\nBYE - Exit the command shell\r\nDEBUG - Display some debugging data\r\nECHO '
                      b'<text to echo> - Echo text back to the console.\r\nEXIT - Exit the command shell\r\nHELP '
                      b'[<command>] - Display help\r\nHISTORY - Display the command history\r\nINFO - '
                      b'Provides some information about the current terminal.\r\nLOGOUT - Exit the command shell'
                      b'\r\nPARAMS [<params>]* - Echos back the raw received parameters.\r\nPASSWD [<password>] - '
                      b'Pretends to set a console password.\r\nQUIT - Exit the command shell\r\nREPEAT <text to echo> '
                      b'- Echo text back to the console.\r\nTIMEIT <time> <message> - In <time> seconds, display '
                      b'<message>.\r\nTIMER <time> <message> - In <time> seconds, display <message>.\r\nTestServer> ',
                      data)

    def test_hidden_cmd(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('127.0.0.1', self.server.server_port))
        _ = s.recv(2048)
        s.sendall(b'test_user\r\n')
        _ = s.recv(1024)
        s.sendall(b'\r\n')
        _ = s.recv(1024)
        s.sendall(b'term\r\n')
        _ = s.recv(1024)
        s.sendall(b'\r\n')
        data = s.recv(1024)
        s.close()
        self.assertEqual(b'TestServer> term\r\nansi\r\nTestServer> ', data)

    def test_cmd_info(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('127.0.0.1', self.server.server_port))
        _ = s.recv(2048)
        s.sendall(b'test_user\r\n')
        _ = s.recv(1024)
        s.sendall(b'\r\n')
        _ = s.recv(1024)
        s.sendall(b'info\r\n')
        _ = s.recv(1024)
        s.sendall(b'\r\n')
        data = s.recv(1024)
        s.close()
        self.assertEqual(b"TestServer> info\r\nUsername: 'test_user', terminal type: 'ansi'\r\nCommand history:\r\n  "
                         b"''\r\n  'info'\r\nTestServer> ", data)

    def test_cmd_params(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('127.0.0.1', self.server.server_port))
        _ = s.recv(2048)
        s.sendall(b'test_user\r\n')
        _ = s.recv(1024)
        s.sendall(b'\r\n')
        _ = s.recv(1024)
        s.sendall(b'params alpha beta charlie test\r\n')
        _ = s.recv(1024)
        s.sendall(b'\r\n')
        data = s.recv(1024)
        s.close()
        self.assertIn(b"params == ['alpha', 'beta', 'charlie', 'test']", data)

    def test_cmd_timer(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('127.0.0.1', self.server.server_port))
        _ = s.recv(2048)
        s.sendall(b'test_user\r\n')
        _ = s.recv(1024)
        s.sendall(b'\r\n')
        _ = s.recv(1024)
        s.sendall(b'timer 2 testing\r\n')
        _ = s.recv(1024)
        s.sendall(b'\r\n')
        data = s.recv(1024)
        s.close()
        self.assertIn(b'TestServer> timer 2 testing\r\nWaiting 2 seconds...\r\nTestServer> ', data)

    def test_cmd_debug(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('127.0.0.1', self.server.server_port))
        _ = s.recv(2048)
        s.sendall(b'test_user\r\n')
        _ = s.recv(1024)
        s.sendall(b'\r\n')
        _ = s.recv(1024)
        s.sendall(b'debug\r\n')
        _ = s.recv(1024)
        s.sendall(b'\r\n')
        data = s.recv(1024)
        s.close()
        self.assertIn(b'TestServer> debug\r\nTestServer> ', data)

    def test_unknown_cmmd(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('127.0.0.1', self.server.server_port))
        _ = s.recv(2048)
        s.sendall(b'test_user\r\n')
        _ = s.recv(1024)
        s.sendall(b'\r\n')
        _ = s.recv(1024)
        s.sendall(b'unkown command\r\n')
        _ = s.recv(1024)
        s.sendall(b'\r\n')
        data = s.recv(1024)
        s.close()
        self.assertIn(b"Unknown command", data)


if __name__ == '__main__':
    unittest.main()
