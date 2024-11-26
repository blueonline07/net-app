#API for communicating with UI
from torrent import Torrent
from constants import PEER_ID, PEER_IP, PEER_PORT
import os
import shutil
import requests
from client import Downloader
from strategy import TitOrTat
from server import Server
from threading import Thread

class Client:
    def __init__(self):
        self.torrents = {}
        self.downloaders = []
        self.download_threads = []
        self.strategy = TitOrTat()
        self.server = Server(self.torrents, PEER_PORT, self.strategy)
        self.server_thread = None

    def create_torrent_from_file_paths(self, dir, file_paths):
        os.makedirs(dir, exist_ok=True)

        for file_path in file_paths:
            shutil.copy(file_path, dir)
        torrent = Torrent.create_torrent_file(dir)
        self.torrents[torrent.info_hash] = torrent
        # print(os.path.abspath(self.torrent.name + ".torrent"))
    
    def create_torrent_from_dir(self, dir):
        torrent = Torrent.create_torrent_file(dir)
        self.torrents[torrent.info_hash] = torrent
        

    def download(self, index):
        torrent = self.torrents[index]
        peers = requests.get(torrent.announce, params={'info_hash':torrent.info_hash, 'peer_id':self.server.peer_id, 'port':self.server.port, 'event':'started'}).json()
        self.downloaders.append(Downloader(torrent, peers, TitOrTat()))
        self.download_threads.append(Thread(target=self.downloaders[-1].start))

    def stop(self, index):
        torrent = self.torrents[index]
        requests.get(torrent.announce, params={'info_hash':torrent.info_hash, 'peer_id':self.server.peer_id, 'port':self.server.port, 'event':'stopped'})
        self.downloaders[index].stop()

    
    def run_server(self):
        self.server_thread = Thread(target=self.server.start).start()

    def shutdown(self):
        requests.get(self.torrent.announce, params={'info_hash':self.torrent.info_hash, 'peer_id':self.id, 'port':self.port, 'event':'stopped'})
        self.downloader = None
        self.server.join()


if __name__ == '__main__':
    client = Client()
    client.create_torrent_from_dir('downloads')
    client.run_server()