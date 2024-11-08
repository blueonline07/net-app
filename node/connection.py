import socket
from messages import Message
from constants import PEER_IP, PEER_PORT

class P2PConnection:
    def __init__(self, ip = None, port = None):
        self.peer_ip = ip
        self.peer_port = port

    def close(self):
        self.socket.close()


class ClientConnection(P2PConnection):
    def __init__(self, ip = None, port = None):
        super().__init__(ip, port)
        self.connection_state = {
            'interested': False,
            'choked': True
        }
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.socket.connect((self.peer_ip, self.peer_port))
        except ConnectionRefusedError:
            print("Connection refused")
            self.socket.close()
    
    def __repr__(self):
        return f"{self.peer_ip}:{self.peer_port}"
    
class ServerConnection(P2PConnection):
    def __init__(self, ip = PEER_IP, port = PEER_PORT):
        super().__init__()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((ip, port))
        self.socket.listen()
        print(f"Server listening on {ip}:{port}")
    
    def accept_connection(self):
        return self.socket.accept()