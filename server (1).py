import socket

SERVER = "192.168.1.13"
SERVER_PORT = 65000
FORMAT = "utf8"

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
        conn.sendall(filename.encode(FORMAT))
        if filename == "Done":
            break  
        if filename in file_list:
            with open(filename, "rb") as input:
                while True:
                    bytes_read = input.read(4096)
                    if not bytes_read:
                        break
                    conn.sendall(bytes_read)
                    conn.recv(4096)
                conn.sendall(b"Done")
            
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
            print("client address: ", addr)
            print("connection: ", conn.getsockname())
            file_list = load_file_list()
            send_file_list(conn, file_list)
            send_file(conn, file_list)
            print("Connection close.")
            conn.close()
        except: 
            print("Connection close.")
            conn.close()

if __name__ == "__main__":
    main()

