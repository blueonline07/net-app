import hashlib
import bencodepy
import os

PIECE_SIZE = 524288 # 512 KB


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
        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(piece_length - len(buffer))
                if not chunk:
                    break
                buffer += chunk
                if len(buffer) == piece_length:
                    pieces.append(hashlib.sha1(buffer).digest())
                    buffer = b""

    # Add final piece if buffer is not empty
    if buffer:
        pieces.append(hashlib.sha1(buffer).digest())
    
    return b"".join(pieces)

def create_multifile_torrent(file_paths, tracker_url, piece_length=PIECE_SIZE):
    # Gather file info for the "files" field
    files_info = []
    for file_path in file_paths:
        file_size = os.path.getsize(file_path)
        file_name = os.path.relpath(file_path)  # Relative paths for directory structure
        files_info.append({
            "length": file_size,
            "path": file_name.split(os.sep)  # Split path for torrent format compatibility
        })

    # Generate pieces
    pieces = generate_pieces(file_paths, piece_length)

    # Torrent metadata structure
    torrent_dict = {
        "announce": tracker_url,
        "info": {
            "name": "",  # Name of the torrent, usually the folder name
            "piece length": piece_length,
            "files": files_info,
            "pieces": pieces
        },
    }
    print(torrent_dict)

    # Encode and save as .torrent
    encoded_torrent = bencodepy.encode(torrent_dict)
    torrent_file = ".torrent"
    with open(torrent_file, "wb") as f:
        f.write(encoded_torrent)

    print(f".torrent file created: {torrent_file}")