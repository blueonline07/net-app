from messages import HandshakeMessage, BitfieldMessage, InterestedMessage,RequestMessage, UnchokeMessage, PieceMessage, Message, ChokeMessage
from utils import recv_all, get_bitfield
from constants import PIECE_SIZE, PROTOCOL_NAME, PEER_ID, PEER_PORT
import socket
from threading import Thread
from torrent import Torrent
import random, string, secrets


class Server:
    def __init__(self,torrent_file_name, port, strategy):
        self.torrent, self.pieces = Torrent.from_torrent_file(torrent_file_name)
        self.port = port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.bitfield = bytes(random.choice(b'\x00\x01') for _ in range(14))
        self.strategy = strategy
        characters = string.ascii_letters + string.digits + string.punctuation
        self.peer_id = ''.join(secrets.choice(characters) for _ in range(20))
        
    def start(self):
        self.server.bind(('0.0.0.0', self.port))
        self.server.listen(5)
        print(f"Peer {self.peer_id} listening on {socket.gethostbyname(socket.gethostname())}:{self.port}")
        
        while True:
            conn, addr = self.server.accept()
            print(f"Connection from {addr}")
            nconn = Thread(target=self.handle_conn, args=(conn,))
            nconn.start()

    def handle_conn(self, conn):
        while True:
            first_byte = conn.recv(1)
            if first_byte == b'\x13':
                self.recv_handshake(conn)
            elif first_byte == b'\x00':
                length = int.from_bytes(recv_all(conn, 3), 'big')
                msg = Message.decode(recv_all(conn, length)) 
                if isinstance(msg, RequestMessage):
                    self.recv_request(conn, msg)
                if isinstance(msg, InterestedMessage):
                    ip, port = conn.getpeername()
                    if ip not in self.strategy.get_unchoke_peers(5):
                        conn.sendall(ChokeMessage().encode())
                    else:
                        conn.sendall(UnchokeMessage().encode())
            elif first_byte == b'':
                print("Connection closed")
                conn.close()
                break
    def recv_handshake(self, conn):
        msg = recv_all(conn, 48 + len(PROTOCOL_NAME))
        handshake_rcv = Message.decode(b'\x13' + msg)
        if handshake_rcv.info_hash != self.torrent.info_hash:
            print("Invalid info hash")
            conn.sendall(0xFF)
            conn.close()
        else:
            conn.sendall(b'\x00') #send anything not 0xFF
        
        conn.sendall(HandshakeMessage(PROTOCOL_NAME, self.torrent.info_hash, PEER_ID).encode())
        conn.sendall(BitfieldMessage(self.bitfield).encode())

    def recv_request(self,conn, message):
        piece_index = message.index
        offset = message.begin
        length = message.length

        file_position = piece_index * PIECE_SIZE + offset

        file_index = 0
        while file_position >= self.torrent.files[file_index]['length']:
            file_position -= self.torrent.files[file_index]['length']
            file_index += 1
        
        block = b''
        data_read = length

        while file_index < len(self.torrent.files):
            with open(self.torrent.files[file_index]['path'], 'rb') as f:
                f.seek(file_position)
                temp = f.read(data_read)
                block += temp
            data_read -= len(temp)
            if data_read == 0:
                break
            elif data_read < 0:
                print(piece_index, offset, length, data_read, len(block))
            else:
                file_index += 1
                file_position = 0
        
        conn.sendall(PieceMessage(piece_index, offset, block).encode())
    