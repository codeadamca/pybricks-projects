# SPDX-License-Identifier: MIT
# Copyright (C) 2020 The Pybricks Authors

"""
:class:`RFCOMMServer` can be used to communicate with other Bluetooth RFCOMM
devices that don't support the EV3 mailbox protocol.

It is based on the standard library ``socketserver`` module and attempts to
remain a strict subset of that implementation when it comes to low-level
implementation details.
"""

from _thread import start_new_thread
from bluetooth import BluetoothSocket, RFCOMM

BDADDR_ANY = ""


def str2ba(string, ba):
    """Convert string to Bluetooth address"""
    for i, v in enumerate(string.split(':')):
        ba.b[5-i] = int(v, 16)


def ba2str(ba):
    """Convert Bluetooth address to string"""
    string = []
    for b in ba.b:
        string.append('{:02X}'.format(b))
    string.reverse()
    return ':'.join(string).upper()


class RFCOMMServer:
    """Object that simplifies setting up an RFCOMM socket server.

    This is based on the ``socketserver.SocketServer`` class in the Python
    standard library.
    """
    request_queue_size = 1

    def __init__(self, server_address, RequestHandlerClass):
        self.server_address = server_address
        self.RequestHandlerClass = RequestHandlerClass

        self.socket = BluetoothSocket(RFCOMM)

        try:
            self.socket.bind((server_address[0], server_address[1]))
            # self.server_address = self.socket.getsockname()
            self.socket.listen(self.request_queue_size)
        except:
            self.server_close()
            raise

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.server_close()

    def handle_request(self):
        try:
            request, addr_data = self.socket.accept()
        except OSError:
            return

        try:
            self.process_request(request, addr_data)
        except:
            request.close()
            raise

    def process_request(self, request, client_address):
        self.finish_request(request, client_address)
        request.close()

    def finish_request(self, request, client_address):
        self.RequestHandlerClass(request, client_address, self)

    def server_close(self):
        self.socket.close()


class ThreadingMixIn:
    def process_request_thread(self, request, client_address):
        try:
            self.finish_request(request, client_address)
        finally:
            request.close()

    def process_request(self, request, client_address):
        start_new_thread(self.process_request_thread, (request, client_address))


class ThreadingRFCOMMServer(ThreadingMixIn, RFCOMMServer):
    """Version of :class:`RFCOMMServer` that handles connections in a new
    thread.
    """
    pass


class RFCOMMClient:
    def __init__(self, client_address, RequestHandlerClass):
        self.client_address = client_address
        self.RequestHandlerClass = RequestHandlerClass
        self.socket = BluetoothSocket(RFCOMM)

    def handle_request(self):
        self.socket.connect((self.client_address[0], self.client_address[1]))
        try:
            self.process_request(self.socket, self.client_address)
        except:
            self.socket.close()
            raise

    def process_request(self, request, client_address):
        self.finish_request(request, client_address)
        request.close()

    def finish_request(self, request, client_address):
        self.RequestHandlerClass(request, client_address, self)

    def client_close(self):
        self.socket.close()


class ThreadingRFCOMMClient(ThreadingMixIn, RFCOMMClient):
    pass
