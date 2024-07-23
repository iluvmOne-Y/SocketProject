import socket
import threading
import json
import os

SERVER = "10.123.1.207"
SERVER_PORT = 5000
FORMAT = "utf-8"

def load_file_list():
    with open('file_list.json', 'r') as file:
        return json.load(file)

def get_chunk_size(priority):
    base_size = 4096
    if priority == "CRITICAL":
        return base_size * 10
    elif priority == "HIGH":
        return base_size * 4
    return base_size

def handle_client(conn, addr, file_list):
    print(f"New connection from {addr}")
    try:
        file_list_json = json.dumps(file_list)
        conn.sendall(file_list_json.encode(FORMAT))

        while True:
            data = conn.recv(1024).decode(FORMAT)
            if not data:
                break

            print(f"\rReceived request from {addr}: {data}",end= " ")
            parts = data.split()
            if len(parts) != 2:
                conn.sendall(b"INVALID_REQUEST")
                continue

            filename, priority = parts

            if filename not in file_list:
                conn.sendall(b"FILE_NOT_FOUND")
                continue

            conn.sendall(b"OK")
            file_size = int(file_list[filename])
            chunk_size = get_chunk_size(priority)

            with open(filename, "rb") as f:
                bytes_sent = 0
                while bytes_sent < file_size:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    conn.sendall(chunk)
                    bytes_sent += len(chunk)
                    conn.recv(2)  # Wait for client ACK

            print(f"Finished sending {filename} to {addr}")

    except Exception as e:
        print(f"Error handling client {addr}: {e}")
    finally:
        conn.close()

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((SERVER, SERVER_PORT))
    server.listen()

    print(f"Server is listening on {SERVER}:{SERVER_PORT}")
    
    file_list = load_file_list()

    while True:
        conn, addr = server.accept()
        client_thread = threading.Thread(target=handle_client, args=(conn, addr, file_list))
        client_thread.start()

if __name__ == "__main__":
    main()