import socket
import os
import sys
import signal
import time
import threading
import curses
stdscr = curses.initscr()

SERVER = "10.126.1.232"
SERVER_PORT = 65000
FORMAT = "utf8"

class FileInfo:
    def __init__(self, filename, size):
        self.filename = filename
        self.size = size
        self.bytes_downloaded = 0
        self.priority = "NORMAL"

downloading_file = []
downloaded_file = []
stop_event = threading.Event()
download_lock = threading.Lock()
cursor_positions = {}
client = None

def main():
    global client
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((SERVER, SERVER_PORT))
    try: 
        stdscr.clear()
        file_list_data = client.recv(4096).decode(FORMAT)
        file_list = dict(line.split() for line in file_list_data.splitlines())
        
        stdscr.addstr("Available files: \n")
        for filename, size in file_list.items():
            stdscr.addstr(f"{filename} - {size}\n")
            
        stdscr.refresh()
        file_info_dict = {}
        for filename, size in file_list.items():
            file_size = int(size.rstrip('MB'))
            file_size = file_size * 1024 * 1024
            file_info_dict[filename] = FileInfo(filename, file_size)
        
        input_thread = threading.Thread(target=scan_input_file, args=(file_list, file_info_dict,))
        input_thread.start()
        process(client, file_info_dict)
        
        client.sendall("Done".encode(FORMAT))
        client.recv(3)
    except Exception as e:
        print(f"Error: {e}")
        client.sendall("Done".encode(FORMAT))
        client.recv(3)
        print("Closing...")

def signal_handler(sig, frame):
    stop_event.set()
    if client:
        client.close()
    sys.exit(0)

def scan_input_file(file_list, file_info_dict):
    os.makedirs("output", exist_ok=True)
    while not stop_event.is_set():
        with download_lock:
            with open("input.txt", "r") as input:
                for line in input:
                    filename, priority = line.strip().split()
                    if filename in file_list and filename not in downloaded_file and filename not in downloading_file:
                        file_info = file_info_dict[filename]
                        file_info.priority = priority
                        downloading_file.append(filename)
        time.sleep(2)

def process(client, file_info_dict):
    # time.sleep(2)
    while not stop_event.is_set():
        for filename in downloading_file:
            file_info = file_info_dict[filename]
            output_path = os.path.join("output", filename)
            if file_info.bytes_downloaded == file_info.size:
                downloaded_file.append(filename)
                downloading_file.remove(filename)
            else:
                download_file(client, output_path, file_info)    

def recvall(sock, n):
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
    
    # time.sleep(0.05)
    data_to_send = f"{filename}\n{priority}".encode(FORMAT)
    client.sendall(data_to_send)
    client.recv(3)
    
    if not os.path.exists(output_path):
        open(output_path, "wb").close()   
         
    with open(output_path, "r+b") as output:
        output.seek(file_info.bytes_downloaded)
        if file_info.priority == "CRITICAL":
            chunksize = 1024*200*10
        elif file_info.priority == "HIGH":
            chunksize = 1024*200*4
        else: chunksize = 1024*200
        if file_info.size - file_info.bytes_downloaded < chunksize:
            chunksize = file_info.size - file_info.bytes_downloaded
        bytes_received = recvall(client, chunksize)
        output.write(bytes_received)
        file_info.bytes_downloaded += len(bytes_received)
        percentage = 100 * file_info.bytes_downloaded / file_size
        filename = file_info.filename
        if filename not in cursor_positions:
            cursor_positions[filename] = len(cursor_positions)
        y = cursor_positions[filename]
        stdscr.addstr(y+ 10, 0, f"Downloading {filename} .... {percentage:.2f}%")
        stdscr.refresh()

if __name__ == "__main__":
    try: 
        signal.signal(signal.SIGINT, signal_handler)
        main()
    finally:
        curses.endwin()
