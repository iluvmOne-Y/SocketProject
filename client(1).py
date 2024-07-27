import socket
import os
import sys
import signal

SERVER = "10.126.1.232"
SERVER_PORT = 65000
FORMAT = "utf8"

class FileInfo:
    def __init__(self, filename, size):
        self.filename = filename
        self.size = size
        self.bytes_downloaded = 0

downloaded_files = []
client = None

def main():
    global client
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
            number = size[:-2] if size[-2:] in ["KB", "MB", "GB"] else size[:-1]
            unit = size[-2:] if size[-2:] in ["KB", "MB", "GB"] else size[-1]
            file_size = GetSize(number, unit)
            file_info_dict[filename] = FileInfo(filename, file_size)
        
        handle_input_file(client, file_list, file_info_dict)
    except Exception as e:
        print(f"Error: {e}")
        client.sendall("Done".encode(FORMAT))
        client.recv(1024)
        print("Closing...")
        client.close()

def GetSize(number, unit):
    number = float(number)
    if unit == "B":
        return number
    elif unit == "KB":
        return number * 1024
    elif unit == "MB":
        return number * 1024**2
    elif unit == "GB":
        return number * 1024**3
    else:
        raise ValueError(f"Unrecognized unit: {unit}")

def signal_handler(sig, frame):
    if client:
        client.close()
    sys.exit(0)

def download_file(client, output_path, file_info):
    client.sendall(file_info.filename.encode(FORMAT))
    received = 0
    with open(output_path, "wb") as output:
        while True:
            byte_received = client.recv(4096)
            if byte_received == b"Done":
                break
            client.sendall(b"ACK")
            output.write(byte_received)
            received += len(byte_received)
            percentage = 100 * received / file_info.size
            print(f"\rDownloading {file_info.filename} .... {percentage:.2f}%", end=" ")
        print(f"\rDownloaded {file_info.filename}")

def handle_input_file(client, file_list, file_info_dict):
    os.makedirs("output", exist_ok=True)
    while True:
        with open("input.txt", "r") as input_file:
            files = input_file.read().splitlines()
        for file in files:
            file = file.strip()
            if file in file_list and file not in downloaded_files:
                output_path = os.path.join("output", file)
                download_file(client, output_path, file_info_dict[file])
                downloaded_files.append(file)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    main()
