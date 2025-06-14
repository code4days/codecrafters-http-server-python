import socket  # noqa: F401
from collections import namedtuple
from dataclasses import dataclass


@dataclass
class RequestLine:
    method: str
    target: str
    version: str


@dataclass
class RequestHeaders:
    headers: dict[str, str]


def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!")

    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)
    conn, _ = server_socket.accept()  # wait for client
    request = conn.recv(1024).decode()

    request_headers = {
        header.split(":")[0].strip(): header.split(":")[1].strip()
        for header in request.split("\r\n")[1:-1]
        if header
    }
    rl = RequestLine(*request.split("\r\n")[0].split())
    if rl.target == "/":
        response = "HTTP/1.1 200 OK\r\n\r\n"
    elif rl.target.startswith("/echo/"):
        response_body = rl.target.split("/echo/")[-1]
        response = f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {len(response_body)}\r\n\r\n{response_body}"
    elif rl.target.startswith("/user-agent"):
        response = f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {len(request_headers['User-Agent'])}\r\n\r\n{request_headers['User-Agent']}"
    else:
        response = "HTTP/1.1 404 Not Found\r\n\r\n"
    conn.sendall(response.encode())
    conn.close()


if __name__ == "__main__":
    main()
