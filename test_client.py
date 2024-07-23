import socket
import os
import sys
import signal
import time
import json
import threading

SERVER = "192.168.1.20"
SERVER_PORT = 65000
FORMAT = "utf-8"

class FileInfo:
    def __init__(self, filename, size, priority):
        self.filename = filename
        self.size = size
        self.bytes_downloaded = 0
        self.priority = priority

client = None
downloading_files = {}
download_lock = threading.Lock()

def signal_handler(sig, frame):
    print("\nClosing connection and exiting...")
    if client:
        client.close()
    sys.exit(0)

def scan_input_file(file_list):
    last_modified = 0
    while True:
        try:
            current_modified = os.path.getmtime('input.txt')
            if current_modified > last_modified:
                with open('input.txt', 'r') as file:
                    lines = file.readlines()
                    with download_lock:
                        for line in lines:
                            parts = line.strip().split()
                            if len(parts) != 2:
                                print(f"Invalid input file format: {line.strip()}")
                                continue
                            filename, priority = parts
                            if filename in file_list and filename not in downloading_files:
                                downloading_files[filename] = FileInfo(filename, int(file_list[filename]), priority)
                last_modified = current_modified
        except Exception as e:
            print(f"Error reading input file: {e}")
        time.sleep(2)

def display_progress():
    while True:
        with download_lock:
            os.system('cls' if os.name == 'nt' else 'clear')
            progress_strings = []
            for filename, file_info in downloading_files.items():
                percentage = (file_info.bytes_downloaded / file_info.size) * 100
                progress_strings.append(f"{filename}: {percentage:.2f}%")
            print(" | ".join(progress_strings), end="\r", flush=True)
        time.sleep(0.5)

def download_files(client, output_dir):
    while True:
        with download_lock:
            for filename, file_info in downloading_files.items():
                chunk_size = get_chunk_size(file_info.priority)
                message = f"{filename} {chunk_size}"
                print(f"Sending request to server: {message}")
                client.sendall(message.encode(FORMAT))
                response = client.recv(1024).decode(FORMAT)
                if response == "FILE_NOT_FOUND":
                    print(f"File {filename} not found on server.")
                    continue
                file_path = os.path.join(output_dir, filename)
                with open(file_path, "ab") as f:
                    while file_info.bytes_downloaded < file_info.size:
                        chunk = client.recv(chunk_size)
                        f.write(chunk)
                        file_info.bytes_downloaded += len(chunk)
                        client.sendall(b"OK")
                print(f"Finished downloading {filename}")

def get_chunk_size(priority):
    base_size = 4096
    if priority == "CRITICAL":
        return base_size * 10
    elif priority == "HIGH":
        return base_size * 4
    return base_size

def main():
    global client
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((SERVER, SERVER_PORT))

    signal.signal(signal.SIGINT, signal_handler)

    response = client.recv(4096).decode(FORMAT)
    file_list = json.loads(response)

    threading.Thread(target=scan_input_file, args=(file_list,)).start()
    threading.Thread(target=display_progress).start()
    download_files(client, "output")

if __name__ == "__main__":
    main()
