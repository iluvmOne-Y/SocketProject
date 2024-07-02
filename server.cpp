#include <iostream>
#include <fstream>
#include <thread>
#include <vector>
#include <string>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <cstring>
#include <sys/stat.h>

std::vector<std::string> list_files() {
    return {"5MB.zip", "10MB.zip", "20MB.zip", "50MB.zip"};
}

void send_file(int client_socket, const std::string &filename) {
    struct stat stat_buf;
    int rc = stat(filename.c_str(), &stat_buf);
    if (rc != 0) {
        std::string error = "ERROR: File not found";
        send(client_socket, error.c_str(), error.size(), 0);
        return;
    }

    std::ifstream file(filename, std::ios::binary);
    if (!file.is_open()) {
        std::string error = "ERROR: File not found";
        send(client_socket, error.c_str(), error.size(), 0);
        return;
    }

    int total_size = stat_buf.st_size;
    send(client_socket, std::to_string(total_size).c_str(), std::to_string(total_size).size(), 0);
    char buffer[4096];
    while (file.read(buffer, sizeof(buffer))) {
        send(client_socket, buffer, file.gcount(), 0);
    }
    if (file.gcount() > 0) {
        send(client_socket, buffer, file.gcount(), 0);
    }

    std::string done = "DONE";
    send(client_socket, done.c_str(), done.size(), 0);
}

void handle_client(int client_socket) {
    auto files = list_files();
    std::string files_list;
    for (const auto &file : files) {
        files_list += file + "\n";
    }
    send(client_socket, files_list.c_str(), files_list.size(), 0);

    char buffer[1024];
    while (true) {
        int bytes_received = recv(client_socket, buffer, sizeof(buffer) - 1, 0);
        if (bytes_received <= 0) break;
        buffer[bytes_received] = '\0';
        std::string filename(buffer);
        if (filename == "exit") break;
        send_file(client_socket, filename);
    }
    close(client_socket);
}

void start_server(int server_socket) {
    struct sockaddr_in client_addr;
    socklen_t client_len = sizeof(client_addr);
    while (true) {
        int client_socket = accept(server_socket, (struct sockaddr*)&client_addr, &client_len);
        if (client_socket < 0) {
            std::cerr << "Error accepting connection" << std::endl;
            continue;
        }
        std::cout << "New connection from " << inet_ntoa(client_addr.sin_addr) << std::endl;
        std::thread client_thread(handle_client, client_socket);
        client_thread.detach();
    }
}

int main() {
    int server_socket = socket(AF_INET, SOCK_STREAM, 0);
    if (server_socket == -1) {
        std::cerr << "Error creating socket" << std::endl;
        return -1;
    }

    struct sockaddr_in server_addr;
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(5000);
    server_addr.sin_addr.s_addr = INADDR_ANY;

    if (bind(server_socket, (struct sockaddr*)&server_addr, sizeof(server_addr)) < 0) {
        std::cerr << "Error binding socket" << std::endl;
        return -1;
    }

    if (listen(server_socket, 5) < 0) {
        std::cerr << "Error listening on socket" << std::endl;
        return -1;
    }

    std::cout << "Server listening on port 5000" << std::endl;
    start_server(server_socket);

    close(server_socket);
    return 0;
}
