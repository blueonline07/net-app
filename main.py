from client import Downloader
from server import Server
from peer import Peer
import threading
import argparse
peers = [
    # {'peer_id': PEER_ID, 'ip': '172.18.0.2', 'port': 8001},
    # {'peer_id': PEER_ID, 'ip': '172.18.0.3', 'port': 8002},
    {'peer_id': '12345678901234567890', 'ip': '127.0.0.1', 'port': 8000},
    {'peer_id': '09876543210987654321', 'ip': '127.0.0.1', 'port': 8001},
    # {'peer_id': PEER_ID, 'ip': '127.0.0.1', 'port': 8008},
    # {'peer_id': PEER_ID, 'ip': '127.0.0.1', 'port': 8009},
]

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='CLI for BitTorrent peer')
    parser.add_argument('--torrent',type=str, help='Specify the torrent file to download')
    parser.add_argument('--test', action='store_true', help='test the p2p network')
    parser.add_argument('--runserver', action='store_true', help='Run the server')
    parser.add_argument('--port',type=int, help='Specify the port to run the server on')
    parser.add_argument('--download', action='store_true', help='Download the torrent')
    args = parser.parse_args()
    if args.test:
        peers = [Peer(torrent=args.torrent, port=test_port) for test_port in range(8000, 8005)]
        peer_list = []
        for peer in peers:
            peer_list.append({
                'peer_id':peer.peer_id,
                'ip':'127.0.0.1',
                'port':peer.server.port
            })

        print(peer_list)
        downloader = Downloader(args.torrent, peer_list)
        

    if args.runserver:
        server = Server(torrent_file_name=args.torrent,port=args.port)
        thread = threading.Thread(target=server.start)
        thread.start()
  
    if args.download:
        downloader = Downloader(args.torrent, peers)
        downloader.start()