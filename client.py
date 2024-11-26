from threading import Thread
from constants import PROTOCOL_NAME, PEER_ID, PIECE_SIZE, BLOCK_SIZE
from messages import HandshakeMessage, InterestedMessage, RequestMessage, BitfieldMessage, Message, UnchokeMessage
import socket
import hashlib
from torrent import Torrent
import os


class Downloader:
    def __init__(self, torrent_file, peers, strategy):
        self.torrent = Torrent(torrent_file)
        self.pieces = {index: [] for index in range(len(self.torrent.pieces))}
        self.peers = peers  # TODO: get peers from tracker
        self.downloaded_pieces = [] # list of pieces index that have been downloaded
        self.strategy = strategy
        self.sources = {} # key: conn, value: list of pieces index
        self.requesting = set()
        self.downloading_threads = []

    def start(self):
        conn_threads = []
        for peer in self.peers:
            thread = Thread(target=self.connect_to_peer, args=(peer['peer_id'], peer['ip'], peer['port']))
            thread.start()
            conn_threads.append(thread)
        for t in conn_threads:
            t.join()
        
        # pieces = {k : v for k, v in sorted(self.pieces.items(), key=lambda item: len(item[1]))}
        self.pieces = sorted(self.pieces.items(), key=lambda item: len(item[1]))
        # key: conn, value: list of pieces index
        for piece_index, conns in self.pieces:   #piece = [conn1, conn2, ...]
            if len(conns) > 0:
                for conn in conns:
                    self.send_interested(conn)
                    msg_rcv = conn.recv(5)
                    msg = Message.decode(msg_rcv[4:])
                    if isinstance(msg, UnchokeMessage):
                        self.sources[conn].append(piece_index)
                

        for peer, pieces in self.sources.items():
            thread = Thread(target=self.download_pieces, args=(peer, pieces))
            thread.start()
            self.downloading_threads.append(thread)
        

        if len(self.downloaded_pieces) == len(self.torrent.pieces):
            print("Download completed, you downloaded the whole file")
        else:
            print("Download failed. Some pieces are missing")

        print(self.torrent.files_info)
    
    def connect_to_peer(self,peer_id, ip, port):
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print(f"Connecting to {ip}:{port}")
        client.connect((ip, port))
        self.strategy.init_downloaded_from(ip)
        handshake_rcv, bitfield_rcv = self.send_handshake(client)
        # if handshake_rcv.info_hash != self.torrent.info_hash or handshake_rcv.peer_id != peer_id:
        #     print("Handshake failed")
        #     client.close()
        #     return
        self.sources[client] = []
        for index, byte in enumerate(bitfield_rcv.bitfield):
            if byte == 1:
                self.pieces[index].append(client)

    def send_handshake(self, conn):
        conn.sendall(HandshakeMessage(PROTOCOL_NAME, self.torrent.info_hash, PEER_ID).encode())
        status = conn.recv(1)
        if status == 0xFF:
            print("Handshake failed")
            conn.close()
            return
        handshake_rcv = conn.recv(49 + len(PROTOCOL_NAME))
        handshake_msg = Message.decode(handshake_rcv)
        bitfield_rcv = conn.recv(5 + len(self.pieces))
        bitfield_msg = Message.decode(bitfield_rcv[4:])
        return handshake_msg, bitfield_msg
    
    def request_block(self, conn, piece_index):
        while piece_index in self.requesting:
            pass

        if piece_index in self.downloaded_pieces:
            return False
        else:
            self.requesting.add(piece_index)

        piece = b''
        begin = 0
        print(f"request for piece {piece_index} from {conn.getpeername()}")
        while begin < PIECE_SIZE:
            conn.sendall(RequestMessage(piece_index, begin, BLOCK_SIZE).encode())
            length = int.from_bytes(conn.recv(4), 'big')
            msg_rcv = conn.recv(length)
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
            self.write_to_file(piece_index, piece)
            # write to bitfield, send have message
            self.requesting.remove(piece_index)
            return True
        else:
            self.requesting.remove(piece_index)
            return False

    def download_pieces(self, conn, pieces):
        for piece_index in pieces:
            if self.request_block(conn, piece_index):
                self.downloaded_pieces.append(piece_index)
                ip, port = conn.getpeername()
                self.strategy.inc_peer_downloaded(ip)
                # send have message
    
    def send_interested(self, conn):
        conn.sendall(InterestedMessage().encode())


    def write_to_file(self, piece_index, piece):
        dir_name = 'repo/'
        file_position = piece_index * PIECE_SIZE

        file_index = 0
        while file_position >= self.torrent.files_info[file_index]['length']:
            file_position -= self.torrent.files_info[file_index]['length']
            file_index += 1
        
        data_writed = len(piece)
        start = 0
        while file_index < len(self.torrent.files_info):
            os.makedirs(os.path.dirname(dir_name + self.torrent.files_info[file_index]['path']), exist_ok=True)
            with open(dir_name + self.torrent.files_info[file_index]['path'], 'ab') as f:
                f.seek(file_position)
                write_size = f.write(piece[start:self.torrent.files_info[file_index]['length'] - file_position])
                data_writed -= write_size
                self.torrent.files_info[file_index]['downloaded'] += write_size
                start = self.torrent.files_info[file_index]['length'] - file_position
            if data_writed == 0:
                break
            elif data_writed < 0:
                print(piece_index, data_writed) #DEBUG
            else:
                file_index += 1
                file_position = 0

    def stop(self):
        for t in self.downloading_threads:
            t.join()