from connection import ServerConnection
from messages import HandshakeMessage, BitfieldMessage, InterestedMessage,RequestMessage, UnchokeMessage, PieceMessage
from utils import parse_torrent_file_info, get_info_hash, recv_all
from constants import PIECE_SIZE, PROTOCOL_NAME, PEER_ID
from time import sleep
from messages import Message

def send_handshake(server):
    recv_all(server.socket, 49 + len(PROTOCOL_NAME))
    server.send_message(HandshakeMessage(PROTOCOL_NAME, get_info_hash('repo.torrent'), PEER_ID))
    server.send_message(BitfieldMessage(b'\x01\x00\x00\x00\x01\x01\x00\x01\x01\x00\x01\x01'))

def receive_msg(server):
    length = recv_all(server.socket,  4)
    length = int.from_bytes(length, 'big')
    if length == 0:
        return
    message = recv_all(server.socket,  length)
    message = Message.decode(message)
    if isinstance(message, InterestedMessage):
        server.send_message(UnchokeMessage())
        server.connection_state['choked'] = False
        server.connection_state['interested'] = True
        receive_request(server)
    elif isinstance(message, RequestMessage):
        receive_request(server, message)


def receive_request(server, message=None):
    piece_index = message.index
    offset = message.begin
    length = message.length

    print(f"Received request for piece {piece_index} offset {offset} length {length}")
    file_position = piece_index * PIECE_SIZE + offset

    files_info = parse_torrent_file_info('repo.torrent')
    
    while file_position > files_info[0]['length']:
        file_position -= files_info[0]['length']
        files_info.pop(0)
        
    with open(files_info[0]['path'], 'rb') as f:
        f.seek(file_position)
        block = f.read(length)
        server.send_message(PieceMessage(piece_index, offset, block))

    print(f"Sent piece {piece_index} offset {offset} length {length}")

def run():
    server = ServerConnection()
    server.accept_connection()
    send_handshake(server)
    while True:
        receive_msg(server)
    


if __name__ == "__main__":
    run()

