import socket  # noqa: F401
from dataclasses import dataclass, field
import threading
import sys
from pathlib import Path
import gzip


@dataclass
class HttpRequest:
    method: str
    target: str
    version: str
    headers: dict[str, str] = field(default_factory=dict)
    body: bytes | None = None


STATUS_OK = "HTTP/1.1 200 OK"
STATUS_NOT_FOUND = "HTTP/1.1 404 Not Found"
STATUS_CREATED = "HTTP/1.1 201 Created"
SUPPORTED_COMPRESSION_TYPES = ["gzip"]


def construct_response(
    status_message: str,
    http_request: HttpRequest | None = None,
    content_type: str | None = None,
    body: str | None = None,
) -> bytes:
    response = f"{status_message}\r\n"

    if not http_request:
        response += "\r\n"
        return response.encode()

    compress_body = False

    if "Accept-Encoding" in http_request.headers:
        for compression_type in http_request.headers["Accept-Encoding"].split(","):
            compression_type = compression_type.strip()
            if compression_type in SUPPORTED_COMPRESSION_TYPES:
                response += f"Content-Encoding: {compression_type}\r\n"
                compress_body = True
                break
    response += f"Content-Type: {content_type}\r\n"
    if compress_body:
        body = gzip.compress(body.encode())
    else:
        body = body.encode()

    response += f"Content-Length: {len(body)}\r\n\r\n"
    response = response.encode()
    response += body

    return response


def parse_request(request: str) -> HttpRequest:
    request_parts = request.split("\r\n")
    http_request = HttpRequest(*request_parts[0].split())
    http_request.headers = {
        header.split(":")[0].strip(): header.split(":")[1].strip()
        for header in request_parts[1:-1]
        if header
    }
    http_request.body = request_parts[-1]

    return http_request


def handle_request(client_socket: socket, storage_path: str) -> None:
    with client_socket:
        while True:
            request = client_socket.recv(1024).decode()
            if not request:
                break

            http_request = parse_request(request)

            if http_request.target == "/":
                response = construct_response(STATUS_OK)

            elif http_request.target.startswith("/echo/"):
                response_body = http_request.target.split("/echo/")[-1]
                response = construct_response(
                    STATUS_OK, http_request, "text/plain", response_body
                )

            elif http_request.target.startswith("/user-agent"):
                response = construct_response(
                    STATUS_OK,
                    http_request,
                    "text/plain",
                    http_request.headers["User-Agent"],
                )

            elif http_request.target.startswith("/files"):
                filename = http_request.target.split("/files/")[-1]
                file_path = Path(storage_path).joinpath(filename)

                if http_request.method == "GET":
                    try:
                        with open(file_path, "r") as f:
                            file_contents = f.read()
                    except FileNotFoundError:
                        response = construct_response(STATUS_NOT_FOUND)
                    else:
                        response = construct_response(
                            STATUS_OK,
                            http_request,
                            "application/octet-stream",
                            file_contents,
                        )

                if http_request.method == "POST":
                    request_body = request.split("\r\n")[-1]
                    with open(file_path, "w") as f:
                        f.write(request_body)
                    response = construct_response(STATUS_CREATED)
            else:
                response = construct_response(STATUS_NOT_FOUND)

            client_socket.sendall(response)

            if (
                "Connection" in http_request.headers
                and http_request.headers["Connection"] == "close"
            ):
                break


def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!")
    storage_path = ""
    if len(sys.argv) > 1 and sys.argv[1] == "--directory":
        storage_path = sys.argv[2]

    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)
    while True:
        client_socket, client_address = server_socket.accept()  # wait for client
        t = threading.Thread(target=handle_request, args=(client_socket, storage_path))
        t.start()


if __name__ == "__main__":
    main()
