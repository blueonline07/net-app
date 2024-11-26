import socket

def tcp_client(host, port, message):
  # Create a TCP/IP socket
  sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

  try:
    # Connect the socket to the server
    sock.connect((host, port))
    print(f"Connected to {host}:{port}")

    # Send data
    sock.sendall(message.encode('utf-8'))
    print(f"Sent: {message}")

    # Receive response
    response = sock.recv(1024)
    print(f"Received: {response.decode('utf-8')}")

  finally:
    # Close the socket
    sock.close()
    print("Connection closed")

if __name__ == "__main__":
  host = 'localhost'  # Server address
  port = 12345        # Server port
  message = 'Hello, Server!'  # Message to send

  tcp_client(host, port, message)