import socket  # noqa: F401
from collections import namedtuple
from dataclasses import dataclass


@dataclass
class RequestLine:
    method: str
    target: str
    version: str


def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!")

    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)
    conn, _ = server_socket.accept()  # wait for client
    request = conn.recv(1024).decode()

    rl = RequestLine(*request.split("\r\n")[0].split())
    if rl.target == "/":
        conn.send(b"HTTP/1.1 200 OK\r\n\r\n")
    else:
        conn.send(b"HTTP/1.1 404 Not Found\r\n\r\n")


if __name__ == "__main__":
    main()
