from threading import Thread
from utils import get_info_hash, create_multifile_torrent, parse_torrent_file_info, recv_all
from constants import PROTOCOL_NAME, PEER_ID, PIECE_SIZE, BLOCK_SIZE
from connection import ClientConnection
from messages import HandshakeMessage, InterestedMessage, RequestMessage, BitfieldMessage, Message
import socket
dir_name = "repo"


peers = [
    {'peer_id': PEER_ID, 'ip': '127.0.0.1', 'port': 8001},
    # {'peer_id': PEER_ID, 'ip': '127.0.0.1', 'port': 8002},
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

def send_handshake(conn):
    conn.sendall(HandshakeMessage(PROTOCOL_NAME, get_info_hash('repo.torrent'), PEER_ID).encode())
    msg_rcv = recv_all(conn, 49 + len(PROTOCOL_NAME) + 5 + len(pieces))
    
    handshake_rcv = Message.decode(msg_rcv[:49 + len(PROTOCOL_NAME)])

    bitfield_rcv = Message.decode(msg_rcv[49 + 4 + len(PROTOCOL_NAME):])

    return handshake_rcv, bitfield_rcv
        
def connect_to_peer(ip, port):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((ip, port))
    print(client)
    handshake_rcv, bitfield_rcv = send_handshake(client)
    print(handshake_rcv, bitfield_rcv)

    for index, byte in enumerate(bitfield_rcv.bitfield):
        if byte == 1:
           pieces[index].append((index, client))

def request_piece(conn, piece_index):
    
    begin = 0
    while begin < PIECE_SIZE:
        block_size = min(BLOCK_SIZE, PIECE_SIZE - begin)
        conn.sendall(RequestMessage(piece_index, begin, block_size).encode())
        length = recv_all(conn, 4)

        msg_rcv = recv_all(conn, int.from_bytes(length, 'big'))
        
        write_to_file(piece_index, begin, Message.decode(msg_rcv).block)
        if Message.decode(msg_rcv).block == b'':
            break
        begin += BLOCK_SIZE

def write_to_file(piece_index, offset, block):
    files_info = parse_torrent_file_info('repo.torrent')
    file_position = piece_index * PIECE_SIZE + offset
    while len(files_info) and file_position > files_info[0]['length']:
        file_position -= files_info[0]['length']
        files_info.pop(0)
    if len(files_info) == 0:
        return
    print(file_position, block)
    with open('repo/' + files_info[0]['path'], 'wb') as f:
        f.seek(file_position)
        f.write(block)
        
if __name__ == "__main__":
    # create_multifile_torrent(["test1.txt", "test2.txt", "test3.txt"])  
    create_piece_index_table()
    #handshaking and create piece index table
    threads = []
    for peer in peers:
        thread = Thread(target=connect_to_peer, args=(peer['ip'], peer['port']))
        thread.start()
        threads.append(thread)
    for t in threads:
        t.join()
    
    #request pieces
    pieces.sort(key=lambda x: len(x))
    print(parse_torrent_file_info('repo.torrent'))
    for piece in pieces:
        if len(piece) == 0:
            continue
        request_piece(piece[0][1], piece[0][0])
    
    print("Finished")