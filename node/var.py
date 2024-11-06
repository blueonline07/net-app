from constants import PIECE_SIZE, TRACKER_URL

TORRENT = {
    "announce": TRACKER_URL,
    "info": {
        "name": "repo",
        "files": []
    },
    "piece length": PIECE_SIZE,
    "pieces": b""
}