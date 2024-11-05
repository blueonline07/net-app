# tracker.py
import socket
import threading
import pickle

# Dictionary to hold peers by file ID
file_peers = {}

def handle_client(conn, addr):
    try:
        data = conn.recv(1024)
        if not data:
            return
        request = pickle.loads(data)
        file_id = request['file_id']
        peer_info = request['peer_info']

        # Register peer and send peer list
        if file_id not in file_peers:
            file_peers[file_id] = []
        if peer_info not in file_peers[file_id]:
            file_peers[file_id].append(peer_info)

        conn.sendall(pickle.dumps(file_peers[file_id]))
    except Exception as e:
        print(f"Error handling client {addr}: {e}")
    finally:
        conn.close()

def start_tracker(host='127.0.0.1', port=8000):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tracker_socket:
        tracker_socket.bind((host, port))
        tracker_socket.listen()
        print(f"Tracker listening on {host}:{port}")

        while True:
            conn, addr = tracker_socket.accept()
            threading.Thread(target=handle_client, args=(conn, addr)).start()

if __name__ == "__main__":
    start_tracker()
