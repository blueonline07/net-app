# client.py
import socket
from threading import Thread
from utils import get_info_hash, create_multifile_torrent

TRACKER_URL = 'localhost:8000'
REPOSITORY_PATH = 'repository/'


peers = [
    {'peer_id': 'peer1', 'ip': '127.0.0.1', 'port': 8001},
    # {'peer_id': 'peer2', 'ip': '127.0.0.1', 'port': 8002},
    # {'peer_id': 'peer3', 'ip': '127.0.0.1', 'port': 8003}
]

def handle_message(message, **kwargs):
    id = int.from_bytes(message[4])
    match id:
        case 0:
            print("Choke")
        case 1:
            print("Unchoke")
        case 2:
            print("Interested")
        case 3:
            print("Not Interested")
        case 4:
            print("Have")
        case 5:
            print("Bitfield")
        case 6:
            print("Request")
        case 7:
            print("Piece")
        case 8:
            print("Cancel")
        case 9:
            print("Port")
        case _:
            print("Unknown message")

def save_piece(torrent, index, piece_data):
    piece_length = torrent["piece_length"]
    offset = index * piece_length
    for file_info in torrent["files"]:
        if offset < file_info["length"]:
            with open(file_info["path"], "r+b") as f:
                f.seek(offset)
                f.write(piece_data[:file_info["length"] - offset])
                piece_data = piece_data[file_info["length"] - offset:]
                if not piece_data:
                    break
        offset -= file_info["length"]
        
def connect_to_peer(peer_id, ip, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((ip, port))
            print(f"Connected to {ip}:{port}")
            connection_state = {
                'im_choking': True,
                'im_interested': False,
                'peer_choking': True,
                'peer_interested': False
            }

            # Send handshake message
            pstr = 'BitTorrent protocol'
            pstrlen = len(pstr).to_bytes(1, byteorder='big')
            info_hash = get_info_hash('.torrent')
            peer_id = peer_id.encode('ascii')
            s.sendall(pstrlen + pstr.encode('ascii') + b'\x00' * 8 + info_hash + peer_id)
            print(s.recv(1024))
            
            # TODO: check if peer_id and info_hash are correct

            # Send interested message
            interested = b'\x00\x00\x00\x01\x02'
            s.sendall(interested)
            # TODO: handle response


        except Exception as e:
            print(e)
        
        
if __name__ == "__main__":
    create_multifile_torrent(["test1.txt", "test2.txt", "test3.txt"], TRACKER_URL)  # Replace with server IP
    threads = [Thread(target=connect_to_peer, args=(peer['peer_id'], peer["ip"], peer["port"])) for peer in peers]
    [t.start() for t in threads]
