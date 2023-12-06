"""Server API.

This module currently only implements `OSCThreadServer`, a thread based server.
"""
import logging
from threading import Thread, Event

import os
import re
import inspect
from sys import platform
from time import sleep, time
from functools import partial
from select import select
import socket

from dmx.oscpy import __version__
from dmx.oscpy.parser import read_packet, UNICODE
from dmx.oscpy.client import send_bundle, send_message
from dmx.oscpy.stats import Stats


logger = logging.getLogger(__name__)


def ServerClass(cls):
    """Decorate classes with for methods implementing OSC endpoints.

    This decorator is necessary on your class if you want to use the
    `address_method` decorator on its methods, see
    `:meth:OSCThreadServer.address_method`'s documentation.
    """
    cls_init = cls.__init__

    def __init__(self, *args, **kwargs):
        cls_init(self, *args, **kwargs)

        for m in dir(self):
            meth = getattr(self, m)
            if hasattr(meth, '_address'):
                server, address, sock, get_address = meth._address
                server.bind(address, meth, sock, get_address=get_address)

    cls.__init__ = __init__
    return cls


__FILE__ = inspect.getfile(ServerClass)


class OSCThreadServer(object):
    """A thread-based OSC server.

    Listens for osc messages in a thread, and dispatches the messages
    values to callbacks from there.

    The '/_oscpy/' namespace is reserved for metadata about the OSCPy
    internals, please see package documentation for further details.
    """

    def __init__(
        self, drop_late_bundles=False, timeout=0.01, advanced_matching=False,
        encoding='', encoding_errors='strict', default_handler=None, intercept_errors=True,
        validate_message_address=True
    ):
        """Create an OSCThreadServer.

        - `timeout` is a number of seconds used as a time limit for
          select() calls in the listening thread, optiomal, defaults to
          0.01.
        - `drop_late_bundles` instruct the server not to dispatch calls
          from bundles that arrived after their timetag value.
          (optional, defaults to False)
        - `advanced_matching` (defaults to False), setting this to True
          activates the pattern matching part of the specification, let
          this to False if you don't need it, as it triggers a lot more
          computation for each received message.
        - `encoding` if defined, will be used to encode/decode all
          strings sent/received to/from unicode/string objects, if left
          empty, the interface will only accept bytes and return bytes
          to callback functions.
        - `encoding_errors` if `encoding` is set, this value will be
          used as `errors` parameter in encode/decode calls.
        - `default_handler` if defined, will be used to handle any
          message that no configured address matched, the received
          arguments will be (address, *values).
        - `intercept_errors`, if True, means that exception raised by
          callbacks will be intercepted and logged. If False, the handler
          thread will terminate mostly silently on such exceptions.
        - `validate_message_address`, if True, require received messages
          to have an address beginning with the specified OSC address
          pattern of '/'. Set to False to accept messages from
          implementations that ignore the address pattern specification.
        """
        self._must_loop = True
        self._termination_event = Event()

        self.addresses = {}
        self.sockets = []
        self.timeout = timeout
        self.default_socket = None
        self.drop_late_bundles = drop_late_bundles
        self.advanced_matching = advanced_matching
        self.encoding = encoding
        self.encoding_errors = encoding_errors
        self.default_handler = default_handler
        self.intercept_errors = intercept_errors
        self.validate_message_address = validate_message_address

        self.stats_received = Stats()
        self.stats_sent = Stats()

        t = Thread(target=self._run_listener)
        t.daemon = True
        t.start()
        self._thread = t

        self._smart_address_cache = {}
        self._smart_part_cache = {}

    def bind(self, address, callback, sock=None, get_address=False):
        """Bind a callback to an osc address.

        A socket in the list of existing sockets of the server can be
        given. If no socket is provided, the default socket of the
        server is used, if no default socket has been defined, a
        RuntimeError is raised.

        Multiple callbacks can be bound to the same address.
        """
        if not sock and self.default_socket:
            sock = self.default_socket
        elif not sock:
            raise RuntimeError('no default socket yet and no socket provided')

        if isinstance(address, UNICODE) and self.encoding:
            address = address.encode(
                self.encoding, errors=self.encoding_errors)

        if self.advanced_matching:
            address = self.create_smart_address(address)

        callbacks = self.addresses.get((sock, address), [])
        cb = (callback, get_address)
        if cb not in callbacks:
            callbacks.append(cb)
        self.addresses[(sock, address)] = callbacks

    def create_smart_address(self, address):
        """Create an advanced matching address from a string.

        The address will be split by '/' and each part will be converted
        into a regexp, using the rules defined in the OSC specification.
        """
        cache = self._smart_address_cache

        if address in cache:
            return cache[address]

        else:
            parts = address.split(b'/')
            smart_parts = tuple(
                re.compile(self._convert_part_to_regex(part)) for part in parts
            )
            cache[address] = smart_parts
            return smart_parts

    def _convert_part_to_regex(self, part):
        cache = self._smart_part_cache

        if part in cache:
            return cache[part]

        else:
            r = [b'^']
            for i, _ in enumerate(part):
                # getting a 1 char byte string instead of an int in
                # python3
                c = part[i:i + 1]
                if c == b'?':
                    r.append(b'.')
                elif c == b'*':
                    r.append(b'.*')
                elif c == b'[':
                    r.append(b'[')
                elif c == b'!' and r and r[-1] == b'[':
                    r.append(b'^')
                elif c == b']':
                    r.append(b']')
                elif c == b'{':
                    r.append(b'(')
                elif c == b',':
                    r.append(b'|')
                elif c == b'}':
                    r.append(b')')
                else:
                    r.append(c)

            r.append(b'$')

            smart_part = re.compile(b''.join(r))

            cache[part] = smart_part
            return smart_part

    def unbind(self, address, callback, sock=None):
        """Unbind a callback from an OSC address.

        See `bind` for `sock` documentation.
        """
        if not sock and self.default_socket:
            sock = self.default_socket
        elif not sock:
            raise RuntimeError('no default socket yet and no socket provided')

        if isinstance(address, UNICODE) and self.encoding:
            address = address.encode(
                self.encoding, errors=self.encoding_errors)

        callbacks = self.addresses.get((sock, address), [])
        to_remove = []
        for cb in callbacks:
            if cb[0] == callback:
                to_remove.append(cb)

        while to_remove:
            callbacks.remove(to_remove.pop())

        self.addresses[(sock, address)] = callbacks

    def listen(
        self, address='localhost', port=0, default=False, family='inet'
    ):
        """Start listening on an (address, port).

        - if `port` is 0, the system will allocate a free port
        - if `default` is True, the instance will save this socket as the
          default one for subsequent calls to methods with an optional socket
        - `family` accepts the 'unix' and 'inet' values, a socket of the
          corresponding type will be created.
          If family is 'unix', then the address must be a filename, the
          `port` value won't be used. 'unix' sockets are not defined on
          Windows.

        The socket created to listen is returned, and can be used later
        with methods accepting the `sock` parameter.
        """
        if family == 'unix':
            family_ = socket.AF_UNIX
        elif family == 'inet':
            family_ = socket.AF_INET
        else:
            raise ValueError(
                "Unknown socket family, accepted values are 'unix' and 'inet'"
            )

        sock = socket.socket(family_, socket.SOCK_DGRAM)
        if family == 'unix':
            addr = address
        else:
            addr = (address, port)
        sock.bind(addr)
        self.sockets.append(sock)
        if default and not self.default_socket:
            self.default_socket = sock
        elif default:
            raise RuntimeError(
                'Only one default socket authorized! Please set '
                'default=False to other calls to listen()'
            )
        self.bind_meta_routes(sock)
        return sock

    def close(self, sock=None):
        """Close a socket opened by the server."""
        if not sock and self.default_socket:
            sock = self.default_socket
        elif not sock:
            raise RuntimeError('no default socket yet and no socket provided')

        if platform != 'win32' and sock.family == socket.AF_UNIX:
            os.unlink(sock.getsockname())
        else:
            sock.close()

        if sock == self.default_socket:
            self.default_socket = None

    def getaddress(self, sock=None):
        """Wrap call to getsockname.

        If `sock` is None, uses the default socket for the server.

        Returns (ip, port) for an inet socket, or filename for an unix
        socket.
        """
        if not sock and self.default_socket:
            sock = self.default_socket
        elif not sock:
            raise RuntimeError('no default socket yet and no socket provided')

        return sock.getsockname()

    def stop(self, s=None):
        """Close and remove a socket from the server's sockets.

        If `sock` is None, uses the default socket for the server.

        """
        if not s and self.default_socket:
            s = self.default_socket

        if s in self.sockets:
            read = select([s], [], [], 0)
            s.close()
            if s in read:
                s.recvfrom(65535)
            self.sockets.remove(s)
        else:
            raise RuntimeError('{} is not one of my sockets!'.format(s))

    def stop_all(self):
        """Call stop on all the existing sockets."""
        for s in self.sockets[:]:
            self.stop(s)
        sleep(10e-9)

    def terminate_server(self):
        """Request the inner thread to finish its tasks and exit.

        May be called from an event, too.
        """
        self._must_loop = False

    def join_server(self, timeout=None):
        """Wait for the server to exit (`terminate_server()` must have been called before).

        Returns True if and only if the inner thread exited before timeout."""
        return self._termination_event.wait(timeout=timeout)

    def _run_listener(self):
        """Wrapper just ensuring that the handler thread cleans up on exit."""
        try:
            self._listen()
        finally:
            self._termination_event.set()

    def _listen(self):
        """(internal) Busy loop to listen for events.

        This method is called in a thread by the `listen` method, and
        will be the one actually listening for messages on the server's
        sockets, and calling the callbacks when messages are received.
        """

        match = self._match_address
        advanced_matching = self.advanced_matching
        addresses = self.addresses
        stats = self.stats_received

        def _execute_callbacks(_callbacks_list):
            for cb, get_address in _callbacks_list:
                try:
                    if get_address:
                        cb(address, *values)
                    else:
                        cb(*values)
                except Exception as exc:
                    if self.intercept_errors:
                        logger.error("Unhandled exception caught in oscpy server", exc_info=True)
                    else:
                        raise

        while self._must_loop:

            drop_late = self.drop_late_bundles
            if not self.sockets:
                sleep(.01)
                continue
            else:
                try:
                    read, write, error = select(self.sockets, [], [], self.timeout)
                except (ValueError, socket.error):
                    continue

            for sender_socket in read:
                try:
                    data, sender = sender_socket.recvfrom(65535)
                except Exception as e:
                    print(e)
                    continue

                try:
                    for address, tags, values, offset in read_packet(
                        data, drop_late=drop_late, encoding=self.encoding,
                        encoding_errors=self.encoding_errors,
                        validate_message_address=self.validate_message_address
                    ):
                        stats.calls += 1
                        stats.bytes += offset
                        stats.params += len(values)
                        stats.types.update(tags)

                        matched = False
                        if advanced_matching:
                            for sock, addr in addresses:
                                if sock == sender_socket and match(addr, address):
                                    callbacks_list = addresses.get((sock, addr), [])
                                    if callbacks_list:
                                        matched = True
                                        _execute_callbacks(callbacks_list)
                        else:
                            callbacks_list = addresses.get((sender_socket, address), [])
                            if callbacks_list:
                                matched = True
                                _execute_callbacks(callbacks_list)

                        if not matched and self.default_handler:
                            self.default_handler(address, *values)
                except ValueError:
                    if self.intercept_errors:
                        logger.error("Unhandled ValueError caught in oscpy server", exc_info=True)
                    else:
                        raise

    @staticmethod
    def _match_address(smart_address, target_address):
        """(internal) Check if provided `smart_address` matches address.

        A `smart_address` is a list of regexps to match
        against the parts of the `target_address`.
        """
        target_parts = target_address.split(b'/')
        if len(target_parts) != len(smart_address):
            return False

        return all(
            model.match(part)
            for model, part in
            zip(smart_address, target_parts)
        )

    def send_message(
        self, osc_address, values, ip_address, port, sock=None, safer=False
    ):
        """Shortcut to the client's `send_message` method.

        Use the default_socket of the server by default.
        See `client.send_message` for more info about the parameters.
        """
        if not sock and self.default_socket:
            sock = self.default_socket
        elif not sock:
            raise RuntimeError('no default socket yet and no socket provided')

        stats = send_message(
            osc_address,
            values,
            ip_address,
            port,
            sock=sock,
            safer=safer,
            encoding=self.encoding,
            encoding_errors=self.encoding_errors
        )
        self.stats_sent += stats
        return stats

    def send_bundle(
        self, messages, ip_address, port, timetag=None, sock=None, safer=False
    ):
        """Shortcut to the client's `send_bundle` method.

        Use the `default_socket` of the server by default.
        See `client.send_bundle` for more info about the parameters.
        """
        if not sock and self.default_socket:
            sock = self.default_socket
        elif not sock:
            raise RuntimeError('no default socket yet and no socket provided')

        stats = send_bundle(
            messages,
            ip_address,
            port,
            sock=sock,
            safer=safer,
            encoding=self.encoding,
            encoding_errors=self.encoding_errors
        )
        self.stats_sent += stats
        return stats

    def get_sender(self):
        """Return the socket, ip and port of the message that is currently being managed.
        Warning::

            this method should only be called from inside the handling
            of a message (i.e, inside a callback).
        """
        frames = inspect.getouterframes(inspect.currentframe())
        for frame, filename, _, function, _, _ in frames:
            if function == '_listen' and __FILE__.startswith(filename):
                break
        else:
            raise RuntimeError('get_sender() not called from a callback')

        sock = frame.f_locals.get('sender_socket')
        address, port = frame.f_locals.get('sender')
        return sock, address, port

    def answer(
        self, address=None, values=None, bundle=None, timetag=None,
        safer=False, port=None
    ):
        """Answers a message or bundle to a client.

        This method can only be called from a callback, it will lookup
        the sender of the packet that triggered the callback, and send
        the given message or bundle to it.

        `timetag` is only used if `bundle` is True.
        See `send_message` and `send_bundle` for info about the parameters.

        Only one of `values` or `bundle` should be defined, if `values`
        is defined, `send_message` is used with it, if `bundle` is
        defined, `send_bundle` is used with its value.
        """
        if not values:
            values = []

        sock, ip_address, response_port = self.get_sender()

        if port is not None:
            response_port = port

        if bundle:
            return self.send_bundle(
                bundle, ip_address, response_port, timetag=timetag, sock=sock,
                safer=safer
            )
        else:
            return self.send_message(
                address, values, ip_address, response_port, sock=sock
            )

    def address(self, address, sock=None, get_address=False):
        """Decorate functions to bind them from their definition.

        `address` is the osc address to bind to the callback.
        if `get_address` is set to True, the first parameter the
        callback will receive will be the address that matched (useful
        with advanced matching).

        example:
            server = OSCThreadServer()
            server.listen('localhost', 8000, default=True)

            @server.address(b'/printer')
            def printer(values):
                print(values)

            send_message(b'/printer', [b'hello world'])

        note:
            This won't work on methods as it'll call them as normal
            functions, and the callback won't get a `self` argument.

            To bind a method use the `address_method` decorator.
        """
        def decorator(callback):
            self.bind(address, callback, sock, get_address=get_address)
            return callback

        return decorator

    def address_method(self, address, sock=None, get_address=False):
        """Decorate methods to bind them from their definition.

        The class defining the method must itself be decorated with the
        `ServerClass` decorator, the methods will be bound to the
        address when the class is instantiated.

        See `address` for more information about the parameters.

        example:

            osc = OSCThreadServer()
            osc.listen(default=True)

            @ServerClass
            class MyServer(object):

                @osc.address_method(b'/test')
                def success(self, *args):
                    print("success!", args)
        """
        def decorator(decorated):
            decorated._address = (self, address, sock, get_address)
            return decorated

        return decorator

    def bind_meta_routes(self, sock=None):
        """This module implements osc routes to probe the internal state of a
        live OSCPy server. These routes are placed in the /_oscpy/ namespace,
        and provide information such as the version, the existing routes, and
        usage statistics of the server over time.

        These requests will be sent back to the client's address/port that sent
        them, with the osc address suffixed with '/answer'.

        examples:
            '/_oscpy/version' -> '/_oscpy/version/answer'
            '/_oscpy/stats/received' -> '/_oscpy/stats/received/answer'

        messages to these routes require a port number as argument, to
        know to which port to send to.
        """
        self.bind(b'/_oscpy/version', self._get_version, sock=sock)
        self.bind(b'/_oscpy/routes', self._get_routes, sock=sock)
        self.bind(b'/_oscpy/stats/received', self._get_stats_received, sock=sock)
        self.bind(b'/_oscpy/stats/sent', self._get_stats_sent, sock=sock)

    def _get_version(self, port, *args):
        self.answer(
            b'/_oscpy/version/answer',
            (__version__, ),
            port=port
        )

    def _get_routes(self, port, *args):
        self.answer(
            b'/_oscpy/routes/answer',
            [a[1] for a in self.addresses],
            port=port
        )

    def _get_stats_received(self, port, *args):
        self.answer(
            b'/_oscpy/stats/received/answer',
            self.stats_received.to_tuple(),
            port=port
        )

    def _get_stats_sent(self, port, *args):
        self.answer(
            b'/_oscpy/stats/sent/answer',
            self.stats_sent.to_tuple(),
            port=port
        )
