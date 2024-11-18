#this class is for test only
import secrets
import string
from server import Server

class Peer:
    def __init__(self,torrent, port, strategy):
        
        self.server = Server(torrent, port, strategy)
    
    def __repr__(self):
        return f"peer_id: {self.peer_id} - port: {self.server.port} - bitfield: {self.server.bitfield}"

    def start(self):
        self.server.start()

    

