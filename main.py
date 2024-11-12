from client import Downloader
from server import Peer
import threading
import argparse


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='CLI for BitTorrent peer')
    parser.add_argument('--torrent',type=str, help='Specify the torrent file to download')
    parser.add_argument('--runserver', action='store_true', help='Run the server')
    parser.add_argument('--port',type=int, help='Specify the port to run the server on')
    parser.add_argument('--download', action='store_true', help='Download the torrent')
    args = parser.parse_args()
    if args.runserver:
        peer = Peer(torrent_file_name=args.torrent,port=args.port)
        thread = threading.Thread(target=peer.start)
        thread.start()
  
    if args.download:
        downloader = Downloader(args.torrent)
        downloader.start()