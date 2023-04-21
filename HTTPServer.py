import socketserver
from pathlib import Path

STATUS_REASONS = {
    200: "OK",
    201: "Created",
    400: "Bad Request",
    404: "Not Found"
}

def build_http_response(http_version, status_code, content_bytes=None, content_type=None):
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

    return response

class HTTPRequestHandler(socketserver.StreamRequestHandler):
    HTTP_VERSION = "HTTP/1.1"

    def handle(self):
        # 5.1 Request Line
        request_line = self.rfile.readline().strip().decode("us-ascii")
        request_method, request_uri, http_version = request_line.split(" ")

        # 5.3 Request Header Fields
        header_params = {}
        for header_line in self.rfile:
            if header_line == b"\r\n": break

            header_key, header_value = header_line.strip().decode("us-ascii").split(":", 1)
            header_params[header_key] = header_value
        
        # Begin content (if any)
        if "Content-Length" in header_params:
            content_length = int(header_params["Content-Length"])
            content_bytes = self.rfile.read(content_length)

        if request_method == "GET":
            self.handle_get(request_uri)
        if request_method == "POST":
            self.handle_post(request_uri, content_bytes)

    def check_file_exists(self, request_uri, send_error=True):
        request_path = Path("." + request_uri)
        exists = True

        if not (request_path.exists() and request_path.is_file()):
            if send_error: self.wfile.write(build_http_response(self.HTTP_VERSION, 404))
            exists = False

        return request_path, exists

    def handle_post(self, request_uri, content_bytes):
        request_path, file_exists = self.check_file_exists(request_uri, send_error=False)

        if file_exists:
            with open(request_path, "ab") as f:
                f.write(content_bytes)
                response = build_http_response(self.HTTP_VERSION, 200)
                self.wfile.write(response)
        else:
            with open(request_path, "wb") as f:
                f.write(content_bytes)
                response = build_http_response(self.HTTP_VERSION, 201)
                self.wfile.write(response)
    
    def handle_get(self, request_uri):
        request_path, file_exists = self.check_file_exists(request_uri)
        if file_exists:
            with open(request_path, "rb") as f:
                response = build_http_response(self.HTTP_VERSION, 200, content_bytes=f.read(), content_type="text/plain")
                self.wfile.write(response)

if __name__ == "__main__":
    HOST, PORT = "localhost", 3000

    with socketserver.TCPServer((HOST, PORT), HTTPRequestHandler) as server:
        server.serve_forever()