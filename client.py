import socket
import os
import sys
import signal
import time
import threading
import curses
stdscr = curses.initscr()


SERVER = "192.168.1.6"
SERVER_PORT = 65000
FORMAT = "utf8"

class FileInfo:
    def __init__(self, filename, size):
        self.filename = filename
        self.size = size
        self.bytes_downloaded = 0
        self.priority = "NORMAL"
    # def __crit__(self, critical):
    #     self.priority = critical

pre_download_file = []
downloading_file = []
downloaded_file = []
stop_event = threading.Event()
download_lock = threading.Lock()
cursor_positions = {}
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
        
        input_thread = threading.Thread(target = scan_input_file, args = (file_list, file_info_dict,))
        # download_thread = threading.Thread(target = process, args = (client, file_info_dict,))
        input_thread.start()
        # download_thread.start()
        # download_thread.join()
        
        process(client, file_info_dict) 
        # handle_input_file(client, file_list, file_info_dict)
        client.sendall("Done".encode(FORMAT))
        client.recv(3)
    except: 
        client.sendall("Done".encode(FORMAT))
        client.recv(3)
        print("Closing...")

def signal_handler(sig, frame):
    stop_event.set()
    if client:
        client.close()
    sys.exit(0)

def scan_input_file(file_list, file_info_dict):
    os.makedirs("output", exist_ok= True)
    while not stop_event.is_set():
        with download_lock:
            with open("input.txt", "r+") as input:
                for line in input:
                    filename, priority = line.strip().split()
                    if filename in file_list and filename not in downloaded_file:
                        file_info = file_info_dict[filename]
                        file_info.priority = priority
                        downloading_file.append(filename)
        time.sleep(2)

def process(client, file_info_dict):
    time.sleep(2)
    while not stop_event.is_set():
        with download_lock:
            for filename in downloading_file:
                file_info = file_info_dict[filename]
                output_path = os.path.join("output", filename)
                # for filename in downloading_file:
                #     print(f"{filename}")
                if file_info.bytes_downloaded == file_info.size:
                    # for filename in downloading_file:
                    #     print(f"{filename}")
                    downloaded_file.append(filename)
                    downloading_file.remove(filename)
                else:
                    download_file(client, output_path, file_info)    
      
def recvall(sock, n):
    # Helper function to recv n bytes or return None if EOF is hit
    data = bytearray()
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data.extend(packet)
    return data
def download_file(client, output_path, file_info):   
    chunksize = 0
    file_size = file_info.size
    filename = file_info.filename
    priority = file_info.priority
    # client.sendall(len(filename).encode(FORMAT))
    # client.recv(3)
    # client.sendall(filename.encode(FORMAT))
    # client.recv(len(filename))
    # client.sendall(len(priority))
    # client.recv(3)
    # client.sendall(priority.encode(FORMAT))
    # client.recv(len(priority))
    time.sleep(0.05)
    data_to_send = f"{filename}\n{priority}".encode(FORMAT)
    client.sendall(data_to_send)
    client.recv(6)
    # time.sleep(0.05)
    if not os.path.exists(output_path):
        open(output_path, "wb").close()   
         
    with open(output_path, "r+b") as output:
        output.seek(file_info.bytes_downloaded)
        if file_info.priority == "CRITICAL":
            chunksize = 4096*10
        elif file_info.priority == "HIGH":
            chunksize = 4096*4
        else: chunksize = 4096
        if file_info.size - file_info.bytes_downloaded < chunksize:
            chunksize = file_info.size - file_info.bytes_downloaded
        bytes_received = recvall(client,chunksize)
        # client.sendall(b"ACK")
        output.write(bytes_received)
        #print(f"{len(bytes_received)}")
        file_info.bytes_downloaded += len(bytes_received)
        percentage = 100 * file_info.bytes_downloaded/file_size
        filename = file_info.filename
        if filename not in cursor_positions:
            cursor_positions[filename] = len(cursor_positions)

        y = cursor_positions[filename]
        stdscr.addstr(y, 0, f"Downloading {filename} .... {percentage:.2f}%")
        stdscr.refresh()
        


def handle_input_file(client, file_list, file_info_dict):
    os.makedirs("output", exist_ok= True)
    while True:
        with open("input.txt", "r") as input:
            for line in input:
                filename, priority = line.strip().split()
                if filename in file_list and filename not in downloaded_file:
                    file_info = file_info_dict[filename]
                    file_info.priority = priority
                    downloading_file.append(filename)
            while True:
                if not downloading_file:
                    break
                for filename in downloading_file:
                    file_info = file_info_dict[filename]
                    output_path = os.path.join("output", filename)
                    download_file(client, output_path, file_info)      
        time.sleep(2)
        
                                         
if __name__ == "__main__":
    try: 
        signal.signal(signal.SIGINT, signal_handler)
        main()
    finally:
        curses.endwin()