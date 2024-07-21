import socket
import os
import sys
import signal
import time


SERVER = "192.168.1.20"
SERVER_PORT = 65000
FORMAT = "utf8"

class FileInfo:
    def __init__(self, filename, size):
        self.filename = filename
        self.size = size
        self.bytes_downloaded = 0
        self.priority = "NORMAL"
    def __crit__(self, critical):
        self.priority = critical

downloading_file = []
downloaded_file = []
client = None

def main():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((SERVER, SERVER_PORT))
    try: 
        file_list_data = client.recv(4096).decode(FORMAT)
        file_list = dict(line.split() for line in file_list_data.splitlines())
        
        print("Available files: ")
        for filename, size in file_list.items():
            print(f"{filename} - {size}")
        
        file_info_dict = {}
        for filename, size in file_list.items():
            file_size = int(size.rstrip('MB'))
            file_size = file_size * 1024 * 1024
            file_info_dict[filename] = FileInfo(filename, file_size)
        
        
        # for file_info in file_info_dict.values():
        #     print(f"{file_info.filename} - {file_info.size}")
        
        handle_input_file(client, file_list, file_info_dict)
        client.sendall("Done".encode(FORMAT))
        client.recv(1024)
    except: 
        client.sendall("Done".encode(FORMAT))
        client.recv(1024)
        print("Closing...")

def signal_handler(sig, frame):
    if client:
        client.close()
    sys.exit(0)

def download_file(client, output_path, file_info):
    chunksize = 0
    file_size = file_info.size
    filename = file_info.filename
    client.sendall(filename.encode(FORMAT))
    client.recv(3)
    client.sendall(file_info.priority.encode(FORMAT))
    client.recv(3)
    if not os.path.exists(output_path):
        open(output_path, "wb").close()
            
    with open(output_path, "r+b") as output:
        output.seek(file_info.bytes_downloaded, 0)
        if file_info.priority == "CRITICAL":
            chunksize = 4096*10
        elif file_info.priority == "HIGH":
            chunksize = 4096*4
        else: chunksize = 4096
        bytes_received = client.recv(chunksize)
        client.sendall(b"ACK")
        output.write(bytes_received)
        print(f"{len(bytes_received)}")
        file_info.bytes_downloaded += len(bytes_received)
        percentage = 100 * file_info.bytes_downloaded/file_size
        print(f"\rDownloading {filename} .... {percentage:.2f}%")
        if file_info.bytes_downloaded == file_size:
            downloaded_file.append(filename)
            downloading_file.remove(filename)
           
            
def load_input():
    input_files = {}
    with open("input.txt", 'r') as f:
        for line in f:
            filename, priority = line.strip().split()
            input_files[filename] = priority
    return input_files

def send_input(conn, input_file):
    input_data = "\n".join([f"{filename} {priority}" for filename, priority in input_file.items()])
    conn.sendall(input_data.encode(FORMAT))

def handle_input_file(client, file_list, file_info_dict):
    os.makedirs("output", exist_ok= True)
    while True:
        time.sleep(2)
        with open("input.txt", "r") as input:
            for line in input:
                filename, priority = line.strip().split()
                if filename in file_list and filename not in downloaded_file:
                    file_info = file_info_dict[filename]
                    file_info.priority = priority
                    downloading_file.append(filename)
            # if downloading_file:
            #     for filename in downloading_file:
            #         client.sendall(filename.encode(FORMAT))
            #         client.recv(1024)
            #         file_info = file_info_dict[filename]
            #         client.sendall(file_info.priority.encode(FORMAT))
            #         client.recv(1024)
            #     client.sendall("Done".encode(FORMAT))
            #     client.recv(1024)
            while True:
                if not downloading_file:
                    break
                for filename in downloading_file:
                    file_info = file_info_dict[filename]
                    output_path = os.path.join("output", filename)
                    download_file(client, output_path, file_info)
        
                                         
if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    main()


    
    