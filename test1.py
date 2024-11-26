import socket

def start_server(host='localhost', port=12345):
  with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((host, port))
    s.listen()
    print(f'Server listening on {host}:{port}')
    conn, addr = s.accept()
    with conn:
      print(f'Connected by {addr}')
      while True:
        data = conn.recv(3)
        print(data)
        if not data:
          break
        conn.sendall(data)

if __name__ == "__main__":
  start_server()