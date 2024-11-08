import socket
from messages import Message
from constants import PEER_IP, PEER_PORT

class P2PConnection:
    def __init__(self, ip = None, port = None):
        self.connection_state = {
            'interested': False,
            'choked': True
        },
        self.peer_ip = ip
        self.peer_port = port
        

    def send_message(self, message):
        self.socket.sendall(message.encode())

    def receive_message(self):
        msg = self.socket.recv(1024)
        return Message.decode(msg)


class ClientConnection(P2PConnection):
    def __init__(self, ip = None, port = None):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        super().__init__(ip, port)
        try:
            self.socket.connect((self.peer_ip, self.peer_port))
        except ConnectionRefusedError:
            print("Connection refused")
            self.socket.close()
    
    def __repr__(self):
        return f"{self.peer_ip}:{self.peer_port}"
    
    def close(self):
        self.socket.close()
    
class ServerConnection(P2PConnection):
    def __init__(self, ip = PEER_IP, port = PEER_PORT):
        super().__init__()
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((ip, port))
        self.server.listen(1)
        self.socket = None
        print(f"Server listening on {ip}:{port}")
    
    def accept_connection(self):
        if self.socket == None:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            conn, addr = self.server.accept()
            self.peer_ip = addr[0]
            self.peer_port = addr[1]
            self.socket = conn

    def close(self):
        self.server.close()