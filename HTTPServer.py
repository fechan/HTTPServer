""" HTTPServer that serves up local files. Written as homework for UW Networks & Distributed Computing class

    WARNING: DO NOT USE THIS IN PRODUCTION! This will serve up arbitrary files on your hard drive regardless
    of where they are located.
"""

import socketserver
import sys
from pathlib import Path

STATUS_REASONS = {
    200: "OK",
    201: "Created",
    204: "No Content",
    400: "Bad Request",
    404: "Not Found",
    415: "Unsupported Media Type",
    500: "Internal Server Error",
    501: "Not Implemented"
}

def send_http_response(wfile, http_version, status_code, content_bytes=None, content_type=None):
    """ Send an HTTP response given the response arguments and the TCP socket file handle
    """

    response = ""

    # 6.1 Status-Line
    response += f"{http_version} {status_code} {STATUS_REASONS[status_code]}\r\n"

    # 7 Entity
    if content_bytes:
        response += f"Content-Type: {content_type}\r\n"
        response += f"Content-Length: {len(content_bytes)}\r\n"
    
    # End header
    response += "\r\n"

    # Begin content (if any)
    response = bytes(response, "us-ascii")
    if content_bytes: response += content_bytes

    wfile.write(response)

def generate_error_body(status_code, reason):
    body = f"""<html>
  <body>
    <img src="https://http.cat/{status_code}">
    <p>{reason}</p>
  </body>
</html>
    """

    return bytes(body, encoding="us-ascii")

class HTTPRequestHandler(socketserver.StreamRequestHandler):
    HTTP_VERSION = "HTTP/1.1"
    SUPPORTED_CONTENT_HEADERS = ["Content-Type", "Content-Length"]

    def handle(self):
        try:
            # 5.1 Request Line
            request_line = self.rfile.readline().strip().decode("us-ascii")
            request_method, request_uri, http_version = request_line.split(" ")

            # 5.3 Request Header Fields
            header_params = {}
            for header_line in self.rfile:
                if header_line == b"\r\n": break

                header_key, header_value = header_line.strip().decode("us-ascii").split(": ", 1)
                header_params[header_key] = header_value
            
            # Begin content (if any)
            if "Content-Length" in header_params:
                content_length = int(header_params["Content-Length"])
                content_bytes = self.rfile.read(content_length)
        except Exception:
            reason = f"You sent a bad request to the server!"
            error_body = generate_error_body(400, reason)
            send_http_response(self.wfile, self.HTTP_VERSION, 400, content_bytes=error_body, content_type="text/html")
            print(sys.exc_info()) # print exception info to console if error

        try:
            if request_method == "GET":
                self.handle_get(request_uri)
            elif request_method == "POST":
                self.handle_post(request_uri, content_bytes, header_params["Content-Type"])
            elif request_method == "PUT":
                self.handle_put(request_uri, content_bytes, header_params)
            elif request_method == "DELETE":
                self.handle_delete(request_uri)
        except Exception:
            reason = f"Oh!! My God!! The server broke and there are no monkeys to fix it!"
            error_body = generate_error_body(500, reason)
            send_http_response(self.wfile, self.HTTP_VERSION, 500, content_bytes=error_body, content_type="text/html")
            print(sys.exc_info()) # print exception info to console if error

    def check_file_exists(self, request_uri, send_error=True):
        request_path = Path("." + request_uri)
        exists = True

        if not (request_path.exists() and request_path.is_file()):
            if send_error:
                reason = f"Oh!! My god!! The server couldn't find the requested resource!"
                error_body = generate_error_body(404, reason)
                send_http_response(self.wfile, self.HTTP_VERSION, 404, content_bytes=error_body, content_type="text/html")
            exists = False

        return request_path, exists

    def handle_delete(self, request_uri):
        request_path, file_exists = self.check_file_exists(request_uri)

        if file_exists:
            request_path.unlink()
            send_http_response(self.wfile, self.HTTP_VERSION, 204)

    def handle_put(self, request_uri, content_bytes, header_params):
        # we are required to handle Content-* headers we don't understand with 501 Not Implemented
        for param in header_params:
            if param.startswith("Content-") and param not in self.SUPPORTED_CONTENT_HEADERS:
                reason = f"`{param}` HTTP header is not supported by this server, and the HTTP/1.1 spec does not allow us to ignore it for PUT requests."
                error_body = generate_error_body(501, reason)
                send_http_response(self.wfile, self.HTTP_VERSION, 501, content_bytes=error_body, content_type="text/html")
                return

        request_path, file_exists = self.check_file_exists(request_uri, send_error=False)

        with open(request_path, "wb") as f:
            f.write(content_bytes)

            if file_exists:
                send_http_response(self.wfile, self.HTTP_VERSION, 204)
            else:
                send_http_response(self.wfile, self.HTTP_VERSION, 201)

    def handle_post(self, request_uri, content_bytes, content_type):
        # we are not allowed to POST anything that isn't text/plain according to the homework rubric
        if content_type != "text/plain":
            reason = f"The server does not support POST for requests that aren't of type text/plain according to the homework rubric."
            error_body = generate_error_body(415, reason)
            send_http_response(self.wfile, self.HTTP_VERSION, 415, content_bytes=error_body, content_type="text/html")
            return

        request_path, file_exists = self.check_file_exists(request_uri, send_error=False)

        if file_exists:
            with open(request_path, "ab") as f:
                f.write(content_bytes)
                send_http_response(self.wfile, self.HTTP_VERSION, 204)
        else:
            with open(request_path, "wb") as f:
                f.write(content_bytes)
                send_http_response(self.wfile, self.HTTP_VERSION, 201)
    
    def handle_get(self, request_uri):
        request_path, file_exists = self.check_file_exists(request_uri)
        if file_exists:
            with open(request_path, "rb") as f:
                extension = request_path.suffix
                if extension == ".txt":
                    send_http_response(self.wfile, self.HTTP_VERSION, 200, content_bytes=f.read(), content_type="text/plain")
                elif extension in [".png", ".gif", ".jpeg"]:
                    send_http_response(self.wfile, self.HTTP_VERSION, 200, content_bytes=f.read(), content_type=f"image/{extension[1:]}")
                else:
                    # send file as generic binary content
                    send_http_response(self.wfile, self.HTTP_VERSION, 200, content_bytes=f.read(), content_type=f"application/octet-stream")

if __name__ == "__main__":
    HOST, PORT = "localhost", 3001

    with socketserver.TCPServer((HOST, PORT), HTTPRequestHandler) as server:
        server.serve_forever()