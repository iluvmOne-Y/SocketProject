import socket
import threading

SERVER = "10.126.1.232"
SERVER_PORT = 65000
FORMAT = "utf8"

class FileInfo:
    def __init__(self, filename, size):
        self.filename = filename
        self.size = size
        self.bytes_send = 0
        self.priority = "NORMAL"

def load_file_list():
    file_list = {}
    with open("file_list.txt", 'r') as f:
        for line in f:
            filename, size = line.strip().split()
            file_list[filename] = size
    return file_list

def send_file_list(conn, file_list):
    file_list_data = "\n".join([f"{filename} {size}" for filename, size in file_list.items()])
    conn.sendall(file_list_data.encode(FORMAT))

def send_file(conn, file_list, file_info_dict):
    while True:
        data = conn.recv(1024).decode(FORMAT).strip()
        if data == "Done":
            conn.sendall(b"ACK")
            break
        
        parts = data.split('\n')
        filename = parts[0]
        priority = parts[1] if len(parts) > 1 else None
        
        conn.sendall(b"ACK")
        if filename in file_list:
            file_info = file_info_dict[filename]
            file_info.priority = priority
            with open(filename, "rb") as input:
                input.seek(file_info.bytes_send)
                if file_info.priority == "CRITICAL":
                    chunksize = 4096*10
                elif file_info.priority == "HIGH":
                    chunksize = 4096*4
                else: chunksize = 4096
                if file_info.size - file_info.bytes_send < chunksize:
                    chunksize = file_info.size - file_info.bytes_send
                bytes_read = input.read(chunksize)
                file_info.bytes_send += len(bytes_read)
                conn.sendall(bytes_read)

def recvThread(conn, addr):
    try:
        print("client address: ", addr)
        print("connection: ", conn.getsockname())
        file_list = load_file_list()
        send_file_list(conn, file_list)
        
        file_info_dict = {}
        
        for filename, size in file_list.items():
            file_size = int(size.rstrip('MB'))
            file_size = file_size * 1024 * 1024
            file_info_dict[filename] = FileInfo(filename, file_size)
        
        send_file(conn, file_list, file_info_dict)
        print("Connection close.")
        conn.close()
    except Exception as e:
        print(f"Error: {e}")
        print("Connection close.")
        conn.close()

def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((SERVER, SERVER_PORT))
    s.listen()

    print("Server side")
    print("Server: ", SERVER, SERVER_PORT)
    print("Waiting for client.")
    while True:
        conn, addr = s.accept()
        thread = threading.Thread(target=recvThread, args=(conn, addr))
        thread.start()

if __name__ == "__main__":
    main()
