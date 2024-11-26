from messages import HandshakeMessage, BitfieldMessage, InterestedMessage,RequestMessage, UnchokeMessage, PieceMessage, Message, ChokeMessage
from utils import  generate_pieces
from constants import PIECE_SIZE, PROTOCOL_NAME
import socket
from threading import Thread
from torrent import Torrent
import random, string, secrets



def get_bitfield(torrent):
    total_length = sum(file["length"] for file in torrent.files_info)
    num_pieces = total_length // PIECE_SIZE + 1

    bitfield = bytearray(num_pieces)
    files = []

    for file in torrent.files_info:
        files.append(file["path"])
    
    pieces = generate_pieces(files)
    original_pieces = torrent.pieces
    
    for (i, piece) in enumerate(pieces):
        if piece in original_pieces:
            bitfield[i] ^= 0x01
    
    return bitfield


class Server:
    def __init__(self, torrents , port, strategy):
        # self.torrent = Torrent(torrent_file_name)
        self.torrents = torrents # {info_hash: torrent}
        self.conns = {} # {conn: torrent}
        self.port = port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

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
            nconn = Thread(target=self.recv_handshake, args=(conn,))
            nconn.start()


    def handle_connection(self, conn):
        while True:
            data = conn.recv(4)
            if data == b'':
                print("No data received, closing connection")
                conn.close()
                return
            length = int.from_bytes(data, 'big')
            msg_data = conn.recv(length)
            msg = Message.decode(msg_data)
            if isinstance(msg, RequestMessage):
                self.recv_request(conn, msg)
            elif isinstance(msg, InterestedMessage):
                # ip, port = conn.getpeername()
                # if ip not in self.strategy.get_unchoke_peers(5):
                #     conn.sendall(ChokeMessage().encode())
                # else:
                #     conn.sendall(UnchokeMessage().encode())
                conn.sendall(UnchokeMessage().encode())   #test only, rm this on final

    def recv_handshake(self, conn):
        msg = conn.recv(49 + len(PROTOCOL_NAME))
        handshake_rcv = Message.decode(b'\x13' + msg[1:])
        if handshake_rcv.info_hash not in self.torrents:
            print("Invalid info hash")
            conn.sendall(b'\xFF')
            conn.close()
            return
        else:
            conn.sendall(b'\x00') #send anything not 0xFF
            self.conns[conn] = self.torrents[handshake_rcv.info_hash]
            conn.sendall(HandshakeMessage(PROTOCOL_NAME, handshake_rcv.info_hash, self.peer_id).encode())
            conn.sendall(BitfieldMessage(get_bitfield(self.conns[conn])) .encode())
            Thread(target=self.handle_connection, args=(conn,)).start()
        
        

    def recv_request(self, conn, message):
        piece_index = message.index
        offset = message.begin
        length = message.length

        file_position = piece_index * PIECE_SIZE + offset

        file_index = 0
        while file_position >= self.conns[conn].files_info[file_index]['length']:
            file_position -= self.conns[conn].files_info[file_index]['length']
            file_index += 1
        
        block = b''
        data_read = length

        while file_index < len(self.conns[conn].files_info):
            with open(self.conns[conn].files_info[file_index]['path'], 'rb') as f:
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
    