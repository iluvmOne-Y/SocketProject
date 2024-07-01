import socket
import os

def download_file(client_socket, filename):
    os.makedirs('output', exist_ok=True)
    total_size = int(client_socket.recv(1024).decode('utf-8'))  # Receive total file size from server
    received_size = 0
    with open(os.path.join('output', filename), 'wb') as file:
        while chunk := client_socket.recv(4096):
            if chunk == b"DONE":
                break
            file.write(chunk)
            received_size += len(chunk)
            progress = (received_size / total_size) * 100
            print(f"Downloading {filename} .... {progress:.2f}%")
def main():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('127.0.0.1', 5000))  # Replace '127.0.0.1' with the actual IP address of the server
    
    files = client_socket.recv(1024).decode('utf-8')
    print("Available files:")
    print(files)
    
    while True:
        filename = input("Enter filename to download (or 'exit' to quit): ")
        if filename == 'exit':
            client_socket.sendall(filename.encode('utf-8'))
            break
        client_socket.sendall(filename.encode('utf-8'))
        download_file(client_socket, filename)
        print(f"{filename} downloaded successfully.")

    client_socket.close()

if __name__ == "__main__":
    main()
