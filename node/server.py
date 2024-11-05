import socket
import threading
from utils import get_info_hash
from constants import PROTOCOL_NAME, PEER_ID

# Define the server host and the ports to listen on
HOST = '127.0.0.1'
PORTS = [8001, 8002, 8003]  # List of ports to listen on

def handle_message(message):
    id = int.from_bytes(message[4])
    match id:
        case 0:
            print("Choke")
        case 1:
            print("Unchoke")
        case 2:
            print("Interested")
        case 3:
            print("Not Interested")
        case 4:
            print("Have")
        case 5:
            print("Bitfield")
        case 6:
            print("Request")
        case 7:
            print("Piece")
        case 8:
            print("Cancel")
        case 9:
            print("Port")
        case _:
            print("Unknown message")


# Function to handle connections on a specific port
def start_server(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((HOST, port))
        server_socket.listen()
        print(f"Server listening on {HOST}:{port}")

        while True:
            client_socket, client_address = server_socket.accept()
            with client_socket:
                print(f"Connected by {client_address} on port {port}")

                while True:
                    data = client_socket.recv(1024)
                    if not data:
                        break
                    if data[:20] == len(PROTOCOL_NAME).to_bytes(1) + PROTOCOL_NAME.encode('ascii'):
                        info_hash = get_info_hash('.torrent')
                        peer_id = PEER_ID.encode('ascii')
                        client_socket.sendall(len(PROTOCOL_NAME).to_bytes(1) + PROTOCOL_NAME.encode('ascii') + b'\x00' * 8 + info_hash + peer_id)
                    else:
                        handle_message(data)

# Start a thread for each port
for port in PORTS:
    thread = threading.Thread(target=start_server, args=(port,))
    thread.start()
