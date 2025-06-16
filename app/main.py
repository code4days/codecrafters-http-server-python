import socket  # noqa: F401
from dataclasses import dataclass
import threading
import sys
from pathlib import Path


@dataclass
class RequestLine:
    method: str
    target: str
    version: str


def handle_request(client_socket, storage_path):
    with client_socket:
        request = client_socket.recv(1024).decode()

        rl = RequestLine(*request.split("\r\n")[0].split())
        request_headers = {
            header.split(":")[0].strip(): header.split(":")[1].strip()
            for header in request.split("\r\n")[1:-1]
            if header
        }

        if rl.target == "/":
            response = "HTTP/1.1 200 OK\r\n\r\n"
        elif rl.target.startswith("/echo/"):
            response_body = rl.target.split("/echo/")[-1]
            response = f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {len(response_body)}\r\n\r\n{response_body}"
        elif rl.target.startswith("/user-agent"):
            response = f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {len(request_headers['User-Agent'])}\r\n\r\n{request_headers['User-Agent']}"
        elif rl.target.startswith("/files"):
            filename = rl.target.split("/files/")[-1]
            try:
                with open(Path(storage_path).joinpath(filename), "r") as f:
                    file_contents = f.read()
            except FileNotFoundError:
                response = "HTTP/1.1 404 Not Found\r\n\r\n"
            else:
                response = f"HTTP/1.1 200 OK\r\nContent-Type: application/octet-stream\r\nContent-Length: {len(file_contents)}\r\n\r\n{file_contents}"
        else:
            response = "HTTP/1.1 404 Not Found\r\n\r\n"

        client_socket.sendall(response.encode())


def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!")
    storage_path = ""
    if len(sys.argv) > 1 and sys.argv[1] == "--directory":
        storage_path = sys.argv[2]

    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)
    while True:
        client_socket, client_address = server_socket.accept()  # wait for client
        print(f"connected to {client_address}")
        t = threading.Thread(target=handle_request, args=(client_socket, storage_path))
        t.start()


if __name__ == "__main__":
    main()
