"""
This is a basic implementation of a client for a P2P network.
"""

import socket
import sys
import threading


class P2PNetwork(object):
    peers = ['127.0.0.1']


def update_peers(peers_string):
    P2PNetwork.peers = peers_string.split(',')[:-1]


class Client(object):

    def __init__(self, address):

        self.socket = self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Make the connection
        self.socket.connect((address, 5000))
        self.byte_size = 1024
        self.peers = []
        print('==> Connected to server.')

        client_listener_thread = threading.Thread(target=self.send_message)
        client_listener_thread.start()

        while True:
            try:
                data = self.receive_message()
                if not data:
                    print("==> Server disconnected.")
                    break
                elif data[0:1] == '\x11':
                    print('==> Got peers.')
                    update_peers(data[1:])
                else:
                    print("[#] " + data)
            except ConnectionError as error:
                print("==> Server disconnected.")
                print('\t--' + str(error))
                break

    # TODO Correct when a peer that is not the server is disconnected
    def send_message(self):
        while True:
            message = input()
            message = str(self.socket.getsockname()) + " >> " + message
            self.socket.send(message.encode('utf-8'))

    def receive_message(self):
        try:
            data = self.socket.recv(self.byte_size)
            return data.decode('utf-8')
        except KeyboardInterrupt:
            self.send_disconnect_signal()

    def send_disconnect_signal(self):
        print('==> Disconnected from server.')
        self.socket.send("q".encode('utf-8'))
        sys.exit()


class Server(object):

    def __init__(self, byte_size):
        try:
            # List with connections to the server
            self.connections = []

            # List of peers connected
            self.peers = []

            # Socket instantiation and setup
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # Bind socket to local host
            self.socket.bind(('127.0.0.1', 5000))

            self.socket.listen(1)

            self.byte_size = byte_size

            print('==> Server running.')

            # Listen to new connections
            while True:
                connection_handler, ip_port_tuple = self.socket.accept()

                # Add the new peer and send to clients the new list
                self.peers.append(ip_port_tuple)
                self.send_peers()
                self.connections.append(connection_handler)

                # Initialize the handler thread
                handler_thread = threading.Thread(target=self.handler, args=(connection_handler, ip_port_tuple,))
                handler_thread.daemon = True
                handler_thread.start()

                print('==> {} connected.'.format(ip_port_tuple))
        except Exception as exception:
            print(exception)
            sys.exit()

    def handler(self, connection_handler, ip_port_tuple):
        try:
            while True:
                data = connection_handler.recv(self.byte_size)
                # Check if the peer wants to disconnect
                for connection in self.connections:
                    if data and data.decode('utf-8') == 'cmd_show_peers':
                        connection.send(('---' + str(self.peers)).encode('utf-8'))
                    elif data:
                        connection.send(data)
        except ConnectionResetError:
            print("==> " + str(ip_port_tuple) + " disconnected")
            self.connections.remove(connection_handler)
            connection_handler.close()
            self.peers.remove(ip_port_tuple)
            self.send_peers()

    def send_peers(self):
        peer_list = ""
        for peer in self.peers:
            peer_list += str(peer[0]) + ','

        for connection in self.connections:
            connection.send(bytes('\x11' + peer_list, 'utf-8'))

        print('==> Peers sent.')
