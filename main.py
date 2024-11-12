from client import run_client
from server import run_server
import threading
import argparse
from time import sleep


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='CLI for BitTorrent peer')
    parser.add_argument('--port',type=int, help='Specify the port to run the server on')
    parser.add_argument('--download',type=str, help='Specify the torrent file to download')
    args = parser.parse_args()
    thread = threading.Thread(target=run_server, args=(args.port, ))
    thread.start()
  
    if args.download:
        sleep(1)
        run_client(args.download)