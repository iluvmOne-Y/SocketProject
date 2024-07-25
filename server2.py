import socket
import threading

SERVER = "10.123.1.93"
SERVER_PORT = 65000
FORMAT = "utf8"

class FileInfo:
    def __init__(self, filename, size):
        self.filename = filename
        self.size = size
        self.bytes_send = 0
        self.priority = "NORMAL"
    # def update_priority(self, priority):
    #     self.priority = priority

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

# def update_priority(conn, filename, file_info_dict):
#     file_info = file_info_dict[filename]
#     priority = conn.recv(1024).decode(FORMAT)
#     conn.sendall(b"ACK")
#     file_info.priority = priority
        
            
def send_file(conn, file_list, file_info_dict):
    while True:
        data = conn.recv(1024).decode(FORMAT).strip()
        if data == "Done":
            break
        
        print(f"{data}")
        parts = data.split('\n')
        filename = parts[0]
        priority = parts[1] if len(parts) > 1 else None

        conn.sendall(b"ACK")
        if priority:
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
                if file_info.size >= chunksize:
                    size = chunksize
                else: size = file_info.size
                bytes_read = input.read(size)
                file_info.bytes_send += size
                file_info.size -= size
                conn.sendall(bytes_read)
                conn.recv(3)

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
        
        # for file_info in file_info_dict.values():
        #     print(f"{file_info.filename } - {file_info.size}")
        # print("hi")
        # for file_info in file_info_dict.values():
        #     print(f"{file_info.filename } - {file_info.priority}")
        
        send_file(conn, file_list, file_info_dict)
        # print("hi")
        print("Connection close.")
        conn.close()
    except: 
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
        thread = threading.Thread(target= recvThread, args= (conn,addr))
        thread.start()
        
    

if __name__ == "__main__":
    main()


