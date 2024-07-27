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

pre_download_file = []
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
        file_list_data = recv_full_message(client).decode(FORMAT)
        file_list = dict(line.split() for line in file_list_data.splitlines())
        
        print("Available files: ")
        for filename, size in file_list.items():
            print(f"{filename} - {size}")
        
        file_info_dict = {}
        for filename, size in file_list.items():
            file_size = int(size.rstrip('MB'))
            file_size = file_size * 1024 * 1024
            file_info_dict[filename] = FileInfo(filename, file_size)
        
        input_thread = threading.Thread(target=scan_input_file, args=(file_list, file_info_dict,))
        input_thread.start()
        process(client, file_info_dict)
        
        client.sendall("Done".encode(FORMAT))
        recv_ack(client)
    except Exception as e:
        print(f"Error: {e}")
        client.sendall("Done".encode(FORMAT))
        recv_ack(client)
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
                if file_info.bytes_downloaded == file_info.size:
                    downloaded_file.append(filename)
                    downloading_file.remove(filename)
                else:
                    download_file(client, output_path, file_info)    

def recv_full_message(sock):
    data = bytearray()
    while True:
        packet = sock.recv(4096)
        if b'<END>' in packet:
            data.extend(packet.split(b'<END>')[0])
            break
        data.extend(packet)
    return data

def recv_ack(sock):
    data = sock.recv(4096)
    if b'<END>' in data:
        return True
    return False

def download_file(client, output_path, file_info):   
    chunksize = 0
    file_size = file_info.size
    filename = file_info.filename
    priority = file_info.priority
    
    time.sleep(0.05)
    data_to_send = f"{filename}\n{priority}".encode(FORMAT)
    client.sendall(data_to_send + b'<END>')
    recv_ack(client)
    
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
        bytes_received = recv_full_message(client)[:chunksize]
        output.write(bytes_received)
        file_info.bytes_downloaded += len(bytes_received)
        percentage = 100 * file_info.bytes_downloaded / file_size
        filename = file_info.filename
        if filename not in cursor_positions:
            cursor_positions[filename] = len(cursor_positions)

        y = cursor_positions[filename]
        stdscr.addstr(y, 0, f"Downloading {filename} .... {percentage:.2f}%")
        stdscr.refresh()

if __name__ == "__main__":
    try: 
        signal.signal(signal.SIGINT, signal_handler)
        main()
    finally:
        curses.endwin()
Server
python
Sao chép mã
import socket
import threading

SERVER = "192.168.1.6"
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
    conn.sendall(file_list_data.encode(FORMAT) + b'<END>')

def send_file(conn, file_list, file_info_dict):
    while True:
        data = recv_full_message(conn).decode(FORMAT).strip()
        if data == "Done":
            send_ack(conn)
            break
        
        parts = data.split('\n')
        filename = parts[0]
        priority = parts[1] if len(parts) > 1 else None
        
        send_ack(conn)
        if priority:
            send_ack(conn)
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
                conn.sendall(bytes_read + b'<END>')

def recv_full_message(sock):
    data = bytearray()
    while True:
        packet = sock.recv(4096)
        if b'<END>' in packet:
            data.extend(packet.split(b'<END>')[0])
            break
        data.extend(packet)
    return data

def send_ack(sock):
    sock.sendall(b'ACK<END>')

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
