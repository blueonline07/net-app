#this class is for test only
import secrets
import string
import random
from client import Downloader
from server import Server

class Peer:
    def __init__(self,torrent, port):
        characters = string.ascii_letters + string.digits + string.punctuation
        self.peer_id = ''.join(secrets.choice(characters) for _ in range(20))
        self.server = Server(torrent, port)
        # self.client = Downloader(torrent, peers)
        self.bitfield = bytes(random.getrandbits(8) for _ in range(13))
    
    def __repr__(self):
        return f"peer_id: {self.peer_id} - port: {self.server.port}"

    def start(self):
        self.server.start()

    

