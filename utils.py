import hashlib
from constants import PIECE_SIZE

def generate_pieces(files):
    pieces = []
    buffer = b""
    # print(files)
    for file in files:
        try:
            with open(file, "rb") as f:
                while True:
                    chunk = f.read(PIECE_SIZE - len(buffer))
                    if not chunk:
                        break
                    buffer += chunk
                    if len(buffer) == PIECE_SIZE:
                        pieces.append(hashlib.sha1(buffer).digest())
                        buffer = b""
        except FileNotFoundError:
            print(f"File {file} not found")

    # Add final piece if buffer is not empty
    if buffer:
        pieces.append(hashlib.sha1(buffer).digest())
    
    return pieces

