import socket
import threading
SERVER = "192.168.1.20"
SERVER_PORT = 65000
FORMAT = "utf8"

class FileInfo:
    def __init__(self, filename, size):
        self.filename = filename
        self.size = size
        self.bytes_sent = 0
        self.priority = "NORMAL"
    def update_priority(self, priority):
        self.priority = priority
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

def update_priority(conn, filename, file_info_dict):
    file_info = file_info_dict[filename]
    priority = conn.recv(1024).decode(FORMAT)
    conn.sendall(b"ACK")
    file_info.priority = priority
    # for key, file_info in file_info_dict.items():
    #     print(f"Key: {key}, Filename: {file_info.filename}, Priority: {file_info.priority}")
        
            
def send_file(conn, file_list, file_info_dict):
    while True:
        filename = conn.recv(1024).decode(FORMAT)
        conn.sendall(b"ACK")
        update_priority(conn, filename, file_info_dict)
        chunksize = 0
        if filename == "Done":
            break  
        if filename in file_list:
            file_info = file_info_dict[filename]
            with open(filename, "r+b") as input:
                input.seek(file_info.bytes_sent)
                if file_info.priority == "CRITICAL":
                    chunksize = 4096*10
                elif file_info.priority == "HIGH":
                    chunksize = 4096*4
                else: chunksize = 4096
                if file_info.size >= chunksize:
                    size = chunksize
                else: size = file_info.size
                bytes_read = input.read(size)
                file_info.bytes_sent += size
                file_info.size -= size
                conn.sendall(bytes_read)
                conn.recv(3)#ack from client
                file_info.bytes_sent += len(bytes_read)
                file_info.size -= len(bytes_read)
def handle_client(conn, addr):
    print(f"New connection: {addr}")
    file_list = load_file_list()
    send_file_list(conn, file_list)
    
    file_info_dict = {}
    for filename, size in file_list.items():
        file_size = int(size.rstrip('MB')) * 1024 * 1024
        file_info_dict[filename] = FileInfo(filename, file_size)
    
    send_file(conn, file_list, file_info_dict)
    print(f"Connection closed: {addr}")
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
        client_thread = threading.Thread(target=handle_client, args=(conn, addr))
        client_thread.start()

if __name__ == "__main__":
    main()


