from client import Downloader
from server import Server
from peer import Peer
import threading
import argparse
from strategy import TitOrTat
from torrent import Torrent

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='CLI for BitTorrent peer')
    parser.add_argument('--create', type=str, help='Create a torrent file')
    parser.add_argument('--torrent',type=str, help='Specify the torrent file to download')
    parser.add_argument('--test', action='store_true', help='test the p2p network')
    parser.add_argument('--runserver', action='store_true', help='Run the server')
    parser.add_argument('--port',type=int, help='Specify the port to run the server on')
    parser.add_argument('--download', action='store_true', help='Download the torrent')
    args = parser.parse_args()
    if args.create:
        torrent = Torrent.create_torrent_file(args.create)

    if args.test:
        peers = [Peer(torrent=args.torrent, port=test_port, strategy=TitOrTat()) for test_port in range(8000, 8005)]
        threads = [threading.Thread(target=peer.start) for peer in peers]
        peer_list = []
        for peer in peers:
            print(peer)
            peer_list.append({
                'peer_id':peer.server.peer_id,
                'ip':'127.0.0.1',
                'port':peer.server.port
            })
        for thread in threads:
            thread.start()

        downloader = Downloader(args.torrent, peer_list, TitOrTat())
        downloader.start()

    if args.runserver:
        strategy = TitOrTat()
        strategy.test_init_downloaded_from()
        server = Server(torrent_file_name=args.torrent,port=args.port, strategy=strategy)
        thread = threading.Thread(target=server.start)
        thread.start()
  
    if args.download:
        peers = [
            {'ip':'172.18.0.2', 'port':8001},
            {'ip':'172.18.0.4', 'port':8002},
            {'ip':'172.18.0.5', 'port':8003}
        ]
        downloader = Downloader(args.torrent, peers, strategy=TitOrTat())
        downloader.start()