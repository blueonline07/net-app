from threading import Thread
from utils import get_info_hash, create_multifile_torrent, parse_torrent_file_info, recv_all, parse_torrent_pieces_hash
from constants import PROTOCOL_NAME, PEER_ID, PIECE_SIZE, BLOCK_SIZE
from messages import HandshakeMessage, InterestedMessage, RequestMessage, BitfieldMessage, Message
import socket
import hashlib
from torrent import Torrent
dir_name = 'downloads'


peers = [
    # {'peer_id': PEER_ID, 'ip': '172.18.0.2', 'port': 8001},
    # {'peer_id': PEER_ID, 'ip': '172.18.0.3', 'port': 8002},
    {'peer_id': PEER_ID, 'ip': '127.0.0.1', 'port': 8000},
    # {'peer_id': PEER_ID, 'ip': '127.0.0.1', 'port': 8008},
    # {'peer_id': PEER_ID, 'ip': '127.0.0.1', 'port': 8009},
]


def write_to_file(piece_index, piece):
    files_info = parse_torrent_file_info(dir_name + '.torrent')
    file_position = piece_index * PIECE_SIZE
    while len(files_info) and file_position > files_info[0]['length']:
        file_position -= files_info[0]['length']
        files_info.pop(0)
    if len(files_info) == 0:
        return
    if file_position + len(piece) > files_info[0]['length']:
        with open(files_info[0]['path'], 'ab') as f:
            f.seek(file_position)
            f.write(piece[:files_info[0]['length'] - file_position])
        if len(files_info) > 1:
            with open(files_info[1]['path'], 'ab') as f:
                f.write(piece[files_info[0]['length'] - file_position:])
    else:
        with open(files_info[0]['path'], 'ab') as f:
            f.seek(file_position)
            f.write(piece)

class Downloader:
    def __init__(self, torrent_file):
        self.torrent, self.pieces = Torrent.from_torrent_file(torrent_file)
        # self.peers = [] # TODO: get peers from tracker
        self.peers = peers

    def start(self):
        conn_threads = []
        for peer in peers:
            thread = Thread(target=self.connect_to_peer, args=(peer['ip'], peer['port']))
            thread.start()
            conn_threads.append(thread)
        for t in conn_threads:
            t.join()
        
        self.pieces.sort(key=lambda x: len(x))

        demand_peers = {}
        for piece in self.pieces:
            if len(piece) == 0:
                continue
            if piece[0][1] not in demand_peers:
                demand_peers[piece[0][1]] = []
            demand_peers[piece[0][1]].append(piece[0][0])
        
        download_threads = []
        for peer, pieces in demand_peers.items():
            # thread = Thread(target=self.download_pieces, args=(peer, pieces))
            # thread.start()
            # download_threads.append(thread)
            self.download_pieces(peer, pieces)
        
        # for t in download_threads:
        #     t.join()

        print("Finished")
    
    def connect_to_peer(self, ip, port):
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print(f"Connecting to {ip}:{port}")
        client.connect((ip, port))

        handshake_rcv, bitfield_rcv = self.send_handshake(client)
        for index, byte in enumerate(bitfield_rcv.bitfield):
            if byte == 1:
                self.pieces[index].append((index, client))

    def send_handshake(self, conn):
        conn.sendall(HandshakeMessage(PROTOCOL_NAME, self.torrent.info_hash, PEER_ID).encode())
        status = recv_all(conn, 1)
        if status == 0xFF:
            print("Handshake failed")
            conn.close()
            return
        print(len(self.pieces))
        msg_rcv = recv_all(conn, 49 + len(PROTOCOL_NAME) + 5 + len(self.pieces))

        handshake_rcv = Message.decode(msg_rcv[:49 + len(PROTOCOL_NAME)])
        bitfield_rcv = Message.decode(msg_rcv[49 + 4 + len(PROTOCOL_NAME):])
        return handshake_rcv, bitfield_rcv
    
    def request_block(self, conn, piece_index):
        piece = b''
        begin = 0
        print(f"request for piece {piece_index}")
        while begin < PIECE_SIZE:
            block_size = min(BLOCK_SIZE, PIECE_SIZE - begin)
            conn.sendall(RequestMessage(piece_index, begin, block_size).encode())
            length = recv_all(conn, 4)
            msg_rcv = recv_all(conn, int.from_bytes(length, 'big'))
            if msg_rcv == b'' or Message.decode(msg_rcv).block == b'':
                break
            piece += Message.decode(msg_rcv).block
            begin += BLOCK_SIZE
        print(f"received piece {piece_index}")

        piece_hash = hashlib.sha1(piece).digest()
        if self.torrent.pieces[piece_index] == piece_hash:
            print(f"Piece {piece_index} is correct")
            # write_to_file(piece_index, piece, torrent)
            # write to bitfield, send have message

    def download_pieces(self, conn, pieces):
        for piece_index in pieces:
            self.request_block(conn, piece_index)


