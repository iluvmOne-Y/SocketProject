import socket
import threading
import os
import json

SERVER = "172.29.87.93"
SERVER_PORT = 65000
FORMAT = "utf-8"

class FileInfo:
    def __init__(self, filename, size):
        self.filename = filename
        self.size = size
        self.bytes_sent = 0

def load_file_list(filename="file_list.json"):
    with open(filename, 'r') as f:
        return json.load(f)

def handle_client(conn, addr, file_list):
    print(f"New connection from {addr}")
    try:
        conn.sendall(json.dumps(file_list).encode(FORMAT))

        while True:
            data = conn.recv(1024).decode(FORMAT).strip()
            print(f"Received data: '{data}'")

            if not data or data == "DONE":
                print(f"Client {addr} signaled completion or sent empty data")
                break

            try:
                filename, priority = data.split(',')
            except ValueError:
                print(f"Invalid data format received from {addr}: {data}")
                conn.sendall(b"INVALID_FORMAT")
                continue

            print(f"Parsed filename: '{filename}', priority: '{priority}'")

            if filename not in file_list:
                print(f"File {filename} not found for client {addr}")
                conn.sendall(b"FILE_NOT_FOUND")
                continue

            conn.sendall(b"OK")
            file_size = int(file_list[filename])
            chunk_size = get_chunk_size(priority)

            try:
                with open(filename, "rb") as f:
                    bytes_sent = 0
                    while bytes_sent < file_size:
                        chunk = f.read(min(chunk_size, file_size - bytes_sent))
                        if not chunk:
                            break
                        conn.sendall(chunk)
                        bytes_sent += len(chunk)
                        ack = conn.recv(2)
                        if ack != b"OK":
                            print(f"Invalid ACK received from {addr}: {ack}")
                            break
                print(f"Finished sending {filename} to {addr}")
            except IOError as e:
                print(f"Error reading file {filename}: {e}")
                conn.sendall(b"FILE_READ_ERROR")

        print(f"Connection from {addr} closed")
    except Exception as e:
        print(f"Error handling client {addr}: {e}")
    finally:
        conn.close()

def get_chunk_size(priority):
    base_size = 4096
    if priority == "CRITICAL":
        return base_size * 10
    elif priority == "HIGH":
        return base_size * 4
    return base_size

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