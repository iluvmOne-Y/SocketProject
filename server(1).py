import socket

SERVER = "10.126.1.232"
SERVER_PORT = 65000
FORMAT = "utf8"

class FileInfo:
    def __init__(self, filename, size):
        self.filename = filename
        self.size = size
        self.bytes_sent = 0

def load_file_list():
    file_list = {}
    with open("file_list.txt", 'r') as f:
        for line in f:
            filename, size = line.strip().split()
            file_list[filename] = size
    return file_list

def send_file_list(conn, file_list):
    file_list_data = "\n".join([f"{filename} {size}" for filename, size in file_list.items()])
    conn.sendall(file_list_data.encode(FORMAT))

def send_file(conn, file_list):
    while True:
        filename = conn.recv(1024).decode(FORMAT)
        if filename == "Done":
            break  
        if filename in file_list:
            with open(filename, "rb") as input_file:
                while True:
                    bytes_read = input_file.read(4096)
                    if not bytes_read:
                        break
                    conn.sendall(bytes_read)
                    ack = conn.recv(4096)
                    if ack != b"ACK":
                        print("Failed to receive ACK")
                        break
                conn.sendall(b"Done")

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

def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((SERVER, SERVER_PORT))
    s.listen()

    print("Server side")
    print("Server: ", SERVER, SERVER_PORT)
    print("Waiting for client.")
    while True: 
        try: 
            conn, addr = s.accept()
            print("Client address: ", addr)
            print("Connection: ", conn.getsockname())
            file_list = load_file_list()
            send_file_list(conn, file_list)
            
            file_info_dict = {}
            for filename, size in file_list.items():
                number = size[:-2] if size[-2:] in ["KB", "MB", "GB"] else size[:-1]
                unit = size[-2:] if size[-2:] in ["KB", "MB", "GB"] else size[-1]
                file_size = GetSize(number, unit)
                file_info_dict[filename] = FileInfo(filename, file_size)
            
            for filename, file_info in file_info_dict.items():
                print(f"{filename} - {file_info.size}")
            
            send_file(conn, file_list)
            print("Connection closed.")
            conn.close()
        except Exception as e:
            print(f"Error: {e}")
            conn.close()

if __name__ == "__main__":
    main()
