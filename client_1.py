import socket
import os
import sys
import signal

SERVER = "192.168.1.8"
SERVER_PORT = 65000
FORMAT = "utf8"

downloaded_files = []
client = None

class FileInfo:
    def __init__(self, filename, size):
        self.filename = filename
        self.size = size
        self.bytes_downloaded = 0

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
            number = size[:-2] if size[-2:] in ["KB", "MB", "GB"] else size[:-1]
            unit = size[-2:] if size[-2:] in ["KB", "MB", "GB"] else size[-1]
            file_size = GetSize(number, unit)
            file_info_dict[filename] = FileInfo(filename, file_size)
        
        handle_input_file(client, file_list, file_info_dict)
    except:
        client.sendall("Done".encode(FORMAT))
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
    filename = file_info.filename
    file_size = file_info.size
    client.sendall(filename.encode(FORMAT))
    with open(output_path, "wb") as output:
        while True:
            chunksize = 4096
            if file_info.size - file_info.bytes_downloaded < chunksize:
                chunksize = file_info.size - file_info.bytes_downloaded
            if chunksize == 0:
                break
            bytes_received = recvall(client, chunksize)
            output.write(bytes_received)
            file_info.bytes_downloaded += len(bytes_received)
            percentage = 100 * file_info.bytes_downloaded / file_size
            client.sendall(b"ACK")
            print(f"\rDownloading {filename} .... {percentage:.2f}%", end=" ")
        print("\r"+" "*50,end="")
        print(f"\rDownloaded {filename}")

def recvall(sock, n):
    data = bytearray()
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if(data == b"Done"):
            break
        if not packet:
            return None
        data.extend(packet)
    return data

def handle_input_file(client, file_list, file_info_dict):
    os.makedirs("output", exist_ok=True)
    while True:
        with open("input.txt", "r") as input_file:
            files = input_file.read().splitlines()
        for filename in files:
            filename = filename.strip()
            if filename in file_list and filename not in downloaded_files:
                output_path = os.path.join("output", filename)
                download_file(client, output_path, file_info_dict[filename])
                downloaded_files.append(filename)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    main()
