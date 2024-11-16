from threading import Thread
from utils import get_info_hash, create_multifile_torrent, parse_torrent_file_info, recv_all, parse_torrent_pieces_hash
from constants import PROTOCOL_NAME, PEER_ID, PIECE_SIZE, BLOCK_SIZE
from messages import HandshakeMessage, InterestedMessage, RequestMessage, BitfieldMessage, Message
import socket
import hashlib
from torrent import Torrent
from strategy import TitOrTat
dir_name = 'downloads'





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
    def __init__(self, torrent_file, peers):
        self.torrent, self.pieces = Torrent.from_torrent_file(torrent_file)
        # self.peers = [] # TODO: get peers from tracker
        self.peers = peers
        self.downloaded_pieces = [] # list of pieces index that have been downloaded
        self.strategy = TitOrTat(self.peers)

    def start(self):

        conn_threads = []
        for peer in self.peers:
            thread = Thread(target=self.connect_to_peer, args=(peer['ip'], peer['port']))
            thread.start()
            conn_threads.append(thread)
        for t in conn_threads:
            t.join()
        
        self.pieces.sort(key=lambda x: len(x))
        print(self.strategy.get_unchoke_peers(4))
        demand_peers = {}
        for piece in self.pieces:
            if len(piece) == 0:
                continue
            if piece[0][1] not in demand_peers:
                demand_peers[piece[0][1]] = []
            demand_peers[piece[0][1]].append(piece[0][0])
        
        download_threads = []
        for peer, pieces in demand_peers.items():
            thread = Thread(target=self.download_pieces, args=(peer, pieces))
            thread.start()
            download_threads.append(thread)
        
        for t in download_threads:
            t.join()

        if len(self.downloaded_pieces) == len(self.torrent.pieces):
            print("Download completed, you downloaded the whole file")
        else:
            print("Download failed. Some pieces are missing")
    
    def connect_to_peer(self, ip, port):
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print(f"Connecting to {ip}:{port}")
        client.connect((ip, port))

        handshake_rcv, bitfield_rcv = self.send_handshake(client)
        print(bitfield_rcv.bitfield)
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
        msg_rcv = recv_all(conn, 49 + len(PROTOCOL_NAME) + 5 + len(self.pieces))

        handshake_rcv = Message.decode(msg_rcv[:49 + len(PROTOCOL_NAME)])
        bitfield_rcv = Message.decode(msg_rcv[49 + 4 + len(PROTOCOL_NAME):])
        return handshake_rcv, bitfield_rcv
    
    def request_block(self, conn, piece_index):
        if piece_index in self.downloaded_pieces:
            return False
        piece = b''
        begin = 0
        print(f"request for piece {piece_index} from {conn.getpeername()}")
        while begin < PIECE_SIZE:
            conn.sendall(RequestMessage(piece_index, begin, BLOCK_SIZE).encode())
            length = recv_all(conn, 4)
            msg_rcv = recv_all(conn, int.from_bytes(length, 'big'))
            if msg_rcv == b'':
                break
            piece += Message.decode(msg_rcv).block
            if len(Message.decode(msg_rcv).block) < BLOCK_SIZE:
                break
            begin += BLOCK_SIZE
            
        print(f"received piece {piece_index}")
        piece_hash = hashlib.sha1(piece).digest()
        if self.torrent.pieces[piece_index] == piece_hash:
            print(f"Piece {piece_index} is correct")
            # write_to_file(piece_index, piece, torrent)
            # write to bitfield, send have message
            return True
        else:
            return False

    def download_pieces(self, conn, pieces):
        for piece_index in pieces:
            if self.request_block(conn, piece_index):
                self.downloaded_pieces.append(piece_index)
                # send have message
            


