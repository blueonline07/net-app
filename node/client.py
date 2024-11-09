from threading import Thread
from utils import get_info_hash, create_multifile_torrent, parse_torrent_file_info, recv_all, parse_torrent_pieces_hash
from constants import PROTOCOL_NAME, PEER_ID, PIECE_SIZE, BLOCK_SIZE
from messages import HandshakeMessage, InterestedMessage, RequestMessage, BitfieldMessage, Message
import socket
import hashlib
dir_name = 'repo/'


peers = [
    {'peer_id': PEER_ID, 'ip': '127.0.0.1', 'port': 8001},
    # {'peer_id': PEER_ID, 'ip': '127.0.0.1', 'port': 8002},
    # {'peer_id': 'peer3', 'ip': '127.0.0.1', 'port': 8003}
]


def create_piece_index_table():
    pieces = []

    files_info = parse_torrent_file_info('repo.torrent')
    total_size = 0
    for file in files_info:
        total_size += file['length']
    
    total_pieces = total_size // PIECE_SIZE + 1
    for i in range(total_pieces):
        pieces.append([])
    
    return pieces

def send_handshake(conn):
    conn.sendall(HandshakeMessage(PROTOCOL_NAME, get_info_hash('repo.torrent'), PEER_ID).encode())
    msg_rcv = recv_all(conn, 49 + len(PROTOCOL_NAME) + 5 + len(pieces))
    
    handshake_rcv = Message.decode(msg_rcv[:49 + len(PROTOCOL_NAME)])

    bitfield_rcv = Message.decode(msg_rcv[49 + 4 + len(PROTOCOL_NAME):])

    return handshake_rcv, bitfield_rcv
        
def connect_to_peer(ip, port, pieces):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((ip, port))
    print(client)
    handshake_rcv, bitfield_rcv = send_handshake(client)
    print(handshake_rcv, bitfield_rcv)

    for index, byte in enumerate(bitfield_rcv.bitfield):
        if byte == 1:
           pieces[index].append((index, client))

def request_block(conn, piece_index):
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
    pieces_hash = parse_torrent_pieces_hash('repo.torrent')
    piece_hash = hashlib.sha1(piece).digest()
    if pieces_hash[piece_index] == piece_hash:
        print(f"Piece {piece_index} is correct")
        write_to_file(piece_index, piece)

def write_to_file(piece_index, piece):
    files_info = parse_torrent_file_info('repo.torrent')
    file_position = piece_index * PIECE_SIZE
    while len(files_info) and file_position > files_info[0]['length']:
        file_position -= files_info[0]['length']
        files_info.pop(0)
    if len(files_info) == 0:
        return
    if file_position + len(piece) > files_info[0]['length']:
        with open(dir_name + files_info[0]['path'], 'ab') as f:
            f.seek(file_position)
            f.write(piece[:files_info[0]['length'] - file_position])
        if len(files_info) > 1:
            with open(dir_name + files_info[1]['path'], 'ab') as f:
                f.write(piece[files_info[0]['length'] - file_position:])
    else:
        with open(dir_name + files_info[0]['path'], 'ab') as f:
            f.seek(file_position)
            f.write(piece)

        
if __name__ == "__main__":
    # create_multifile_torrent(["test1.txt", "test2.txt", "test3.txt"])  
    pieces = create_piece_index_table()
    #handshaking and create piece index table
    threads = []
    for peer in peers:
        thread = Thread(target=connect_to_peer, args=(peer['ip'], peer['port'], pieces))
        thread.start()
        threads.append(thread)
    for t in threads:
        t.join()
    pieces.sort(key=lambda x: len(x))

    for piece in pieces:
        if len(piece) == 0:
            continue
        request_block(piece[0][1], piece[0][0])
    
    print("Finished")