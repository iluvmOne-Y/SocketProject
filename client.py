import socket
import os
import sys
import signal
import json
import time
import threading
import queue

SERVER = "10.123.1.207"
SERVER_PORT = 5000
FORMAT = "utf-8"

client = None
file_list = {}
download_queue = queue.Queue()
downloading = False

def signal_handler(sig, frame):
    print("\nClosing connection and exiting...")
    if client:
        client.close()
    sys.exit(0)

def get_chunk_size(priority):
    base_size = 4096
    if priority == "CRITICAL":
        return base_size * 10
    elif priority == "HIGH":
        return base_size * 4
    return base_size

def download_file(filename, priority):
    global downloading
    chunk_size = get_chunk_size(priority)
    client.sendall(f"{filename} {priority}".encode(FORMAT))
    response = client.recv(1024).decode(FORMAT)
    
    if response == "FILE_NOT_FOUND":
        print(f"File {filename} not found on server.")
        return

    file_path = os.path.join("output", filename)
    file_size = file_list[filename]
    
    with open(file_path, "wb") as f:
        bytes_downloaded = 0
        while bytes_downloaded < file_size:
            chunk = client.recv(chunk_size)
            if not chunk:
                break
            f.write(chunk)
            bytes_downloaded += len(chunk)
            client.sendall(b"OK")
            
            percentage = (bytes_downloaded / file_size) * 100
            print(f"\rDownloading {filename} ... {percentage:.2f}%",end=" ")
    
    print(f"Finished downloading {filename}")
    downloading = False

def download_manager():
    global downloading
    while True:
        if not downloading and not download_queue.empty():
            filename, priority = download_queue.get()
            print(f"Starting download of {filename} with priority {priority}")
            downloading = True
            download_file(filename, priority)
        else:
            time.sleep(0.1)

def scan_input_file():
    last_modified = 0
    processed_lines = set()
    while True:
        try:
            if os.path.exists('input.txt'):
                current_modified = os.path.getmtime('input.txt')
                if current_modified > last_modified:
                    with open('input.txt', 'r') as file:
                        lines = file.readlines()
                        for line in lines:
                            line = line.strip()
                            if line and line not in processed_lines:
                                parts = line.split()
                                if len(parts) == 2:
                                    filename, priority = parts
                                    if filename in file_list:
                                        download_queue.put((filename, priority))
                                        processed_lines.add(line)
                                        print(f"Added {filename} to download queue with priority {priority}")
                                    else:
                                        print(f"File {filename} is not available on the server.")
                                else:
                                    print(f"Invalid line in input.txt: {line}")
                    last_modified = current_modified
            else:
                print("input.txt does not exist. Creating an empty file.")
                open('input.txt', 'a').close()
        except Exception as e:
            print(f"Error reading input file: {e}")
        time.sleep(2)

def main():
    global client, file_list
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((SERVER, SERVER_PORT))

    signal.signal(signal.SIGINT, signal_handler)

    response = client.recv(4096).decode(FORMAT)
    file_list = json.loads(response)
    print("Available files:")
    for filename, size in file_list.items():
        print(f"{filename}: {size} bytes")

    os.makedirs("output", exist_ok=True)

    threading.Thread(target=scan_input_file, daemon=True).start()
    threading.Thread(target=download_manager, daemon=True).start()

    print("Monitoring input.txt for download requests...")
    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()