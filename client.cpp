#include <iostream>
#include <fstream>
#include <string>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <sys/stat.h>
#include <cstring>

void download_file(int client_socket, const std::string &filename) {
    mkdir("output", 0777);
    char buffer[1024];
    int bytes_received = recv(client_socket, buffer, sizeof(buffer) - 1, 0);
    buffer[bytes_received] = '\0';
    int total_size = std::stoi(buffer);

    int received_size = 0;
    std::ofstream file("output/" + filename, std::ios::binary);
    if (!file.is_open()) {
        std::cerr << "Error opening file for writing" << std::endl;
        return;
    }

    while (true) {
        bytes_received = recv(client_socket, buffer, sizeof(buffer), 0);
        if (bytes_received <= 0) break;
        if (std::string(buffer, bytes_received) == "DONE") break;
        file.write(buffer, bytes_received);
        received_size += bytes_received;
        float progress = (received_size / static_cast<float>(total_size)) * 100;
        std::cout << "Downloading " << filename << " .... " << progress << "%" << std::endl;
    }
    file.close();
}

int main() {
    int client_socket = socket(AF_INET, SOCK_STREAM, 0);
    if (client_socket == -1) {
        std::cerr << "Error creating socket" << std::endl;
        return -1;
    }

    struct sockaddr_in server_addr;
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(5000);
    server_addr.sin_addr.s_addr = inet_addr("127.0.0.1");  

    if (connect(client_socket, (struct sockaddr*)&server_addr, sizeof(server_addr)) < 0) {
        std::cerr << "Error connecting to server" << std::endl;
        return -1;
    }

    char buffer[1024];
    int bytes_received = recv(client_socket, buffer, sizeof(buffer) - 1, 0);
    buffer[bytes_received] = '\0';
    std::cout << "Available files:" << std::endl << buffer << std::endl;

    while (true) {
        std::string filename;
        std::cout << "Enter filename to download (or 'exit' to quit): ";
        std::getline(std::cin, filename);

        if (filename == "exit") {
            send(client_socket, filename.c_str(), filename.size(), 0);
            break;
        }

        send(client_socket, filename.c_str(), filename.size(), 0);
        download_file(client_socket, filename);
        std::cout << filename << " downloaded successfully." << std::endl;
    }

    close(client_socket);
    return 0;
}
