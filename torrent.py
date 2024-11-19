import os
import bencodepy, hashlib
from utils import generate_pieces
from constants import PIECE_SIZE, TRACKER_URL

class Torrent:
    def __init__(self, name, file_paths):
        self.name = name
        self.announce = TRACKER_URL
        self.piece_length = PIECE_SIZE
        self.files = []
        for file_path in file_paths:
            file_size = os.path.getsize(file_path)
            file_name = os.path.relpath(file_path)  # Relative paths for directory structure
            self.files.append({
                "length": file_size,
                "path": file_name
            })
        # Generate pieces
        self.pieces = generate_pieces(file_paths, PIECE_SIZE)
        self.info_hash = hashlib.sha1(bencodepy.encode({"name":self.name, "files":self.files, "piece length":PIECE_SIZE, "pieces":self.pieces})).digest()

    @staticmethod
    def from_torrent_file(torrent_file):
        with open(torrent_file, "rb") as f:
            torrent_dict = bencodepy.decode(f.read())
            torrent_name = torrent_dict[b"info"][b"name"].decode()

            file_paths = []
            files = torrent_dict[b"info"][b"files"]

            total_size = 0
            for file in files:
                file_paths.append(file[b"path"].decode()) 
                total_size += file[b"length"]


            return Torrent(torrent_name, file_paths), {k : [] for k in range(total_size // PIECE_SIZE + 1)}

    @staticmethod
    def create_torrent_file(directory):
        # List all files and directories (shallow)
        entries = os.listdir(directory)

        files = [directory + os.sep + file for file in [entry for entry in entries if os.path.isfile(os.path.join(directory, entry))]]
        pieces = generate_pieces(files, PIECE_SIZE)
        torrent_dict = {
            "announce": TRACKER_URL,
            "info": {
                "name": directory,  # Name of the torrent, usually the folder name
                "files": [{"length": os.path.getsize(file), "path": file} for file in files],
                "piece length": PIECE_SIZE,
                "pieces": pieces
            },
        }
        # Encode and save as .torrent
        encoded_torrent = bencodepy.encode(torrent_dict)
        torrent_file = directory + ".torrent"
        try:
            with open(torrent_file, "wb") as f:
                f.write(encoded_torrent)
                print(f"Torrent file created: {torrent_file}")
        except Exception as e:
            print(f"Error creating torrent file: {e}")
  