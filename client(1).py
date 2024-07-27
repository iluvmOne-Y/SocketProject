import socket
import os
import sys
import signal


SERVER = "10.126.0.108"
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
                number = size[:-2]
                unit = size[-2:]
                file_size = GetSize(number, unit)
                file_info_dict[filename] = FileInfo(filename, file_size)
        
        handle_input_file(client, file_list)
    except: 
        client.sendall("Done".encode(FORMAT))
        client.recv(1024)
        print("Closing...")

def GetSize(number, unit):
    if unit == "KB":
        file_size = number*1024
    elif unit == "MB":
        file_size = number*pow(1024,2)
    elif unit == "GB":
        file_size = number*pow(1024,3)
    return file_size        
    
def signal_handler(sig, frame):
    if client:
        client.close()
    sys.exit(0)

def download_file(client, output_path, file, file_size):
    client.sendall(file.encode(FORMAT))
    # client.recv(1024)
    received = 0
    with open(output_path, "wb") as output:
        while True:
            byte_received = client.recv(4096)
            if byte_received==b"Done":
                break
            client.sendall(b"ACK")
            output.write(byte_received)
            received += len(byte_received)
            percentage = 100 * received/(file_size*1024*1024)
            print(f"\rDownloading {file} .... {percentage:.2f}%",end=" ")
            
        output, filename = os.path.split(output_path)
        print(f"\rDownloading {filename} ")
def handle_input_file(client, file_list):
    os.makedirs("output", exist_ok= True)
    while True:
        with open("input.txt", "r") as input:
            files = input.read().splitlines()
        for file in files:
            file = file.strip()
            if file in file_list:
                if file not in downloaded_files:
                    file_size = int(file_list[file].rstrip('MB'))
                    output_path = os.path.join("output", file)
                    download_file(client, output_path, file, file_size)
                    downloaded_files.append(file)
            

      

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    main()

