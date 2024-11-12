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


def create_piece_index_table(torrent):
    files = torrent.files
    total_size = sum([file['length'] for file in files])
    
    total_pieces = total_size // PIECE_SIZE + 1

    return [[] for _ in range(total_pieces)]

def send_handshake(conn, pieces):
    conn.sendall(HandshakeMessage(PROTOCOL_NAME, get_info_hash(dir_name + '.torrent'), PEER_ID).encode())
    status = recv_all(conn, 1)
    if status == 0xFF:
        print("Handshake failed")
        conn.close()
        return
    print(len(pieces))
    msg_rcv = recv_all(conn, 49 + len(PROTOCOL_NAME) + 5 + len(pieces))

    handshake_rcv = Message.decode(msg_rcv[:49 + len(PROTOCOL_NAME)])
    bitfield_rcv = Message.decode(msg_rcv[49 + 4 + len(PROTOCOL_NAME):])
    return handshake_rcv, bitfield_rcv
        
def connect_to_peer(ip, port, pieces):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print(f"Connecting to {ip}:{port}")
    client.connect((ip, port))

    handshake_rcv, bitfield_rcv = send_handshake(client, pieces)

    # TODO: if peer_id not in peers, close connection

    for index, byte in enumerate(bitfield_rcv.bitfield):
        if byte == 1:
           pieces[index].append((index, client))

def request_block(conn, piece_index, torrent):
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
    if torrent.pieces[piece_index] == piece_hash:
        print(f"Piece {piece_index} is correct")
        # write_to_file(piece_index, piece, torrent)
        # write to bitfield, send have message

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

        
def run_client(torrent_file_name):
    torrent, pieces = Torrent.from_torrent_file(torrent_file_name)
    # torrent =  Torrent('downloads', ["repository/test1.txt", "repository/test2.txt", "repository/test3.txt"])
    # pieces = create_piece_index_table(torrent)
    #handshaking and create piece index table
    threads = []
    for peer in peers:
        thread = Thread(target=connect_to_peer, args=(peer['ip'], peer['port'], pieces))
        thread.start()
        threads.append(thread)
    for t in threads:
        t.join()
    
    pieces.sort(key=lambda x: len(x))
    print(pieces)

    for piece in pieces:
        if len(piece) == 0:
            continue
        request_block(piece[0][1], piece[0][0], torrent)
    
    print("Finished")

# class Client:
#     def __init__(self, torrent_file):
#         self.torrent, self.pieces = Torrent.from_torrent_file(torrent_file)
#         self.threads = []