import socket
import os
import sys
import signal
import time
import json
import threading

SERVER = "172.29.87.93"
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
    while True:
        with open('input.txt', 'r') as file:
            lines = file.readlines()
            with download_lock:
                for line in lines:
                    filename, priority = line.strip().split()
                    if filename in file_list and filename not in downloading_files:
                        downloading_files[filename] = FileInfo(filename, int(file_list[filename]), priority)
        time.sleep(2)

def display_progress():
    while True:
        with download_lock:
            os.system('cls' if os.name == 'nt' else 'clear')
            for filename, file_info in downloading_files.items():
                percentage = (file_info.bytes_downloaded / file_info.size) * 100
                print(f"Downloading {filename} .... {percentage:.2f}%")
        time.sleep(0.5)

def download_files(client, output_dir):
    while True:
        with download_lock:
            if not downloading_files:
                time.sleep(0.1)
                continue

            for filename, file_info in list(downloading_files.items()):
                request = f"{filename},{file_info.priority}"
                print(f"Sending request: '{request}'")
                client.sendall(request.encode(FORMAT))
                response = client.recv(1024).decode(FORMAT).strip()
                print(f"Received response: '{response}'")
                
                if response == "FILE_NOT_FOUND":
                    print(f"File {filename} not found on server")
                    del downloading_files[filename]
                elif response == "INVALID_FORMAT":
                    print(f"Server reported invalid format for {filename}")
                    del downloading_files[filename]
                elif response == "FILE_READ_ERROR":
                    print(f"Server reported error reading {filename}")
                    del downloading_files[filename]
                elif response == "OK":
                    output_path = os.path.join(output_dir, filename)
                    try:
                        with open(output_path, "ab") as f:
                            while file_info.bytes_downloaded < file_info.size:
                                chunk = client.recv(get_chunk_size(file_info.priority))
                                if not chunk:
                                    break
                                f.write(chunk)
                                file_info.bytes_downloaded += len(chunk)
                                client.sendall(b"OK")

                        if file_info.bytes_downloaded >= file_info.size:
                            print(f"Finished downloading {filename}")
                            del downloading_files[filename]
                    except Exception as e:
                        print(f"Error downloading {filename}: {e}")
                        del downloading_files[filename]
                else:
                    print(f"Unexpected response from server: {response}")

        time.sleep(0.1)  # Add a small delay to prevent CPU overuse

def get_chunk_size(priority):
    base_size = 4096
    if priority == "CRITICAL":
        return base_size * 10
    elif priority == "HIGH":
        return base_size * 4
    return base_size

def main():
    global client, file_list

    signal.signal(signal.SIGINT, signal_handler)

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((SERVER, SERVER_PORT))

    file_list = json.loads(client.recv(4096).decode(FORMAT))
    print("Available files:")
    for filename, size in file_list.items():
        print(f"{filename} - {size} bytes")

    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    scan_thread = threading.Thread(target=scan_input_file, args=(file_list,))
    scan_thread.daemon = True
    scan_thread.start()

    progress_thread = threading.Thread(target=display_progress)
    progress_thread.daemon = True
    progress_thread.start()

    download_thread = threading.Thread(target=download_files, args=(client, output_dir))
    download_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        client.sendall(b"DONE")
        client.close()

if __name__ == "__main__":
    main()