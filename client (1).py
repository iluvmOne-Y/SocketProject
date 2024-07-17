import socket
import os
import sys
import signal


SERVER = "10.126.1.239"
SERVER_PORT = 65000
FORMAT = "utf8"

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
        
        handle_input_file(client, file_list)
    except: 
        client.sendall("Done".encode(FORMAT))
        client.recv(1024)
        print("Closing...")

def signal_handler(sig, frame):
    if client:
        client.close()
    sys.exit(0)

def download_file(client, output_path, file, file_size):
    client.sendall(file.encode(FORMAT))
    client.recv(1024)
    received = 0
    with open(output_path, "wb") as output:
        while True:
            byte_received = client.recv(4096)
            if byte_received == b"Done":
                break
            client.sendall(b"ACK")
            output.write(byte_received)
            received += len(byte_received)
            percentage = 100 * received/(file_size*1024*1024)
            print(f"Downloading {file} .... {percentage:.2f}%")
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

