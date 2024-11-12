import hashlib
import bencodepy
import os
from constants import PIECE_SIZE, TRACKER_URL

def recv_all(sock, num_bytes):
    data = b""
    while len(data) < num_bytes:
        packet = sock.recv(num_bytes - len(data))
        if not packet:
            break  # Connection closed
        data += packet
    return data


def get_info_hash(torrent_file):
    with open(torrent_file, "rb") as f:
        torrent_data = f.read()
        torrent_dict = bencodepy.decode(torrent_data)
        info_dict = torrent_dict[b"info"]
        return hashlib.sha1(bencodepy.encode(info_dict)).digest()

def generate_pieces(file_paths, piece_length):
    pieces = []
    buffer = b""
    
    for file_path in file_paths:
        try:
            with open(file_path, "rb") as f:
                while True:
                    chunk = f.read(piece_length - len(buffer))
                    if not chunk:
                        break
                    buffer += chunk
                    if len(buffer) == piece_length:
                        pieces.append(hashlib.sha1(buffer).digest())
                        buffer = b""
        except FileNotFoundError:
            continue

    # Add final piece if buffer is not empty
    if buffer:
        pieces.append(hashlib.sha1(buffer).digest())
    
    return pieces

def parse_torrent_file(torrent_file):
    with open(torrent_file, "rb") as f:
        torrent_data = f.read()
        torrent_dict = bencodepy.decode(torrent_data)
        return torrent_dict
def parse_torrent_pieces_hash(torrent_file):
    with open(torrent_file, "rb") as f:
        torrent_data = f.read()
        torrent_dict = bencodepy.decode(torrent_data)
        return torrent_dict['pieces'.encode('ascii')]
def parse_torrent_file_info(torrent_file):
    with open(torrent_file, "rb") as f:
        torrent_data = f.read()
        torrent_dict = bencodepy.decode(torrent_data)

        files = torrent_dict['info'.encode('ascii')]['files'.encode('ascii')]
        files_info = []
        for file in files:
            files_info.append({
                'length': file['length'.encode('ascii')],
                'path': file['path'.encode('ascii')].decode('ascii')
            })
        return files_info
        

def create_multifile_torrent(name, file_paths):
    # Gather file info for the "files" field
    files_info = []
    for file_path in file_paths:
        file_size = os.path.getsize(file_path)
        file_name = os.path.relpath(file_path)  # Relative paths for directory structure
        files_info.append({
            "length": file_size,
            "path": file_name  # Split path for torrent format compatibility
        })

    # Generate pieces
    pieces = generate_pieces(file_paths, PIECE_SIZE)

    # Torrent metadata structure
    torrent_dict = {
        "announce": TRACKER_URL,
        "info": {
            "name": name,  # Name of the torrent, usually the folder name
            "files": files_info,
        },
        "piece length": PIECE_SIZE,
        "pieces": pieces
    }

    # Encode and save as .torrent
    encoded_torrent = bencodepy.encode(torrent_dict)
    torrent_file = name + ".torrent"
    with open(torrent_file, "wb") as f:
        f.write(encoded_torrent)

    print(f"Torrent file created: {torrent_file}")
    return torrent_file

def get_bitfield(torrent_file):
    files_info = parse_torrent_file_info(torrent_file)
    print(files_info)
    total_length = sum(file["length"] for file in files_info)
    num_pieces = total_length // PIECE_SIZE + 1
    print(total_length, num_pieces)
    bitfield = bytearray(num_pieces)
    files = []

    for file in files_info:
        files.append(file["path"])
    
    pieces = generate_pieces(files, PIECE_SIZE)
    original_pieces = parse_torrent_pieces_hash(torrent_file)
    
    for (i, piece) in enumerate(pieces):
        if piece in original_pieces:
            bitfield[i] ^= 0x01
    
    return bitfield
