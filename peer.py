#this class is for test only
import secrets
import string
from server import Server

class Peer:
    def __init__(self,torrent, port):
        characters = string.ascii_letters + string.digits + string.punctuation
        self.peer_id = ''.join(secrets.choice(characters) for _ in range(20))
        self.server = Server(torrent, port)
    
    def __repr__(self):
        return f"peer_id: {self.peer_id} - port: {self.server.port} - bitfield: {self.server.bitfield}"

    def start(self):
        self.server.start()

    

