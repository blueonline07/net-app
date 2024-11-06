from threading import Thread
from utils import get_info_hash, create_multifile_torrent, parse_torrent_file_info, recv_all
from constants import PROTOCOL_NAME, PEER_ID, PIECE_SIZE, BLOCK_SIZE
from connection import ClientConnection
from messages import HandshakeMessage, InterestedMessage, RequestMessage, BitfieldMessage, Message
import os
from time import sleep
dir_name = "repo"


peers = [
    {'peer_id': PEER_ID, 'ip': '127.0.0.1', 'port': 8001},
    # {'peer_id': 'peer2', 'ip': '127.0.0.1', 'port': 8002},
    # {'peer_id': 'peer3', 'ip': '127.0.0.1', 'port': 8003}
]

pieces = []

def create_piece_index_table():
    files_info = parse_torrent_file_info('repo.torrent')
    total_size = 0
    for file in files_info:
        total_size += file['length']
    
    total_pieces = total_size // PIECE_SIZE + 1
    for i in range(total_pieces):
        pieces.append([])

def send_handshake(client):
    client.send_message(HandshakeMessage(PROTOCOL_NAME, get_info_hash('repo.torrent'), PEER_ID))
    msg_rcv = recv_all(client.socket, 49 + len(PROTOCOL_NAME) + 5 + len(pieces))
    handshake_rcv = Message.decode(msg_rcv[:49 + len(PROTOCOL_NAME)])
    bitfield_rcv = Message.decode(msg_rcv[49 + 4 + len(PROTOCOL_NAME):])
    return handshake_rcv, bitfield_rcv
        
def connect_to_peer(ip, port):
    client = ClientConnection(ip, port)
    _, bitfield_rcv = send_handshake(client)
    

    for index, byte in enumerate(bitfield_rcv.bitfield):
        if byte == 1:
           pieces[index].append((index, ip, port))
    

    pieces.sort(key=lambda x: len(x))
    print(pieces)
    for piece in pieces:
        begin = 0
        while begin < PIECE_SIZE:
            block_size = min(BLOCK_SIZE, PIECE_SIZE - begin)
            if len(piece) == 0:
                break
            client.send_message(RequestMessage(piece[0][0], begin, block_size))
            length = recv_all(client.socket, 4)
            msg_rcv = recv_all(client.socket, int.from_bytes(length, 'big'))
            print(Message.decode(msg_rcv))
            begin += BLOCK_SIZE
    
    client.close()
    
        
if __name__ == "__main__":
    create_multifile_torrent(["test1.txt", "test2.txt", "test3.txt"])  
    create_piece_index_table()
    connect_to_peer('localhost', 8001)
