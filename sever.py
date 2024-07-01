import socket
import threading
import os

def list_files():
    files = ["5MB.zip", "10MB.zip", "20MB.zip", "50MB.zip"]
    return "\n".join(files)

def send_file(client_socket, filename):
    try:
        total_size = os.path.getsize(filename)
        client_socket.sendall(str(total_size).encode('utf-8'))  # Send total file size to client
        sent_size = 0
        with open(filename, "rb") as file:
            while chunk := file.read(4096):
                client_socket.sendall(chunk)
                sent_size += len(chunk)
        client_socket.sendall(b"DONE")
    except FileNotFoundError:
        client_socket.sendall(b"ERROR: File not found")
def handle_client(client_socket):
    files = list_files()
    client_socket.sendall(files.encode('utf-8'))
    
    while True:
        filename = client_socket.recv(1024).decode('utf-8')
        if filename == 'exit':
            break
        send_file(client_socket, filename)
    client_socket.close()
def start_server(server_socket):
    while True:
        client_socket, addr = server_socket.accept()
        print(f"New connection from {addr}")
        client_thread = threading.Thread(target=handle_client, args=(client_socket,))
        client_thread.start()
def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', 5000))
    server_socket.listen(5)
    
    print("Server listening on port 5000")
    
    while True:
        client_socket, addr = server_socket.accept()
        print(f"Connection from {addr}")
        client_thread = threading.Thread(target=handle_client, args=(client_socket,))
        client_thread.start()

if __name__ == "__main__":
    main()
