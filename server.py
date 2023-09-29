import os
import socketserver

# Copyright 2013 Abram Hindle, Eddie Antonio Santos
# Copyright 2023 Sashreek Magan
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Furthermore it is derived from the Python documentation examples thus
# some of the code is Copyright © 2001-2013 Python Software
# Foundation; All Rights Reserved
# http://docs.python.org/2/library/socketserver.html
# run: python freetests.py
# try: curl -v -X GET http://127.0.0.1:8080/
# Sources: 
# https://opensource.stackexchange.com/questions/9199/how-to-label-and-license-derivative-works-made-under-apache-license-version-2-0

class MyWebServer(socketserver.BaseRequestHandler):
    """A simple web server that serves static files."""

    # HTTP Status Codes and their corresponding messages
    CODES = {
        200: 'OK',
        301: 'Moved Permanently',
        400: 'Bad Request',
        404: 'Not Found',
        405: 'Method Not Allowed'
    }

    # Mapping of file extensions to MIME types
    MIME_TYPES = {
        '.html': 'text/html',
        '.css': 'text/css'
    }

    def handle(self):
        """Handle incoming client requests."""
        self.data = self.request.recv(1024).strip()
        if self.data:
            req_method, req_path, _ = self.parse_request(self.data)
            response = self.build_response(req_method, req_path)
            self.request.sendall(response)

    def build_response(self, method, path):
        """Build the response based on request method and path."""
        if method.upper() != 'GET':
            return self.construct_error(405)

        file_path = self.get_path(path)

        if os.path.isdir(file_path) and not path.endswith('/'):
            return self.redirect(path)
        elif not os.path.isfile(file_path):
            return self.construct_error(404)

        with open(file_path, 'rb') as file:
            content = file.read()
        return self.construct_response(200, file_path, content)

    def construct_response(self, code, file_path, content):
        """Construct a response given a status code, file path, and content."""
        mime_type = self.MIME_TYPES.get(os.path.splitext(file_path)[1], 'text/plain')
        headers = {
            "Content-Type": mime_type,
            "Content-Length": str(len(content)),
            "Connection": "close"
        }

        response_line = f"HTTP/1.1 {code} {self.CODES[code]}\r\n"
        headers_str = ''.join([f"{header_name}: {header_value}\r\n" for header_name, header_value in headers.items()])
        
        return f"{response_line}{headers_str}\r\n".encode() + content

    def construct_error(self, code):
        """Construct an error response."""
        content = f"<html><body><h1>{code} {self.CODES[code]}</h1></body></html>".encode()
        return self.construct_response(code, '.html', content)

    def redirect(self, path):
        """Construct a redirection response."""
        headers = {
            "Location": path + '/'
        }
        response_line = f"HTTP/1.1 301 {self.CODES[301]}\r\n"
        headers_str = ''.join([f"{header_name}: {header_value}\r\n" for header_name, header_value in headers.items()])
        return f"{response_line}{headers_str}\r\n".encode()

    def get_path(self, path):
        """Normalize the path and get the corresponding file path."""
        root_dir = os.path.abspath('www') # Get the absolute path of root
        normalized_path = os.path.abspath(os.path.join('www', path.lstrip("/"))) # Get the absolute path of the requested file
        
        # Check if the normalized path is still within the root directory
        if not normalized_path.startswith(root_dir):
            return "invalid_path" # Or any other mechanism to indicate an invalid path

        if os.path.isdir(normalized_path) and path.endswith('/'):
            return os.path.join(normalized_path, 'index.html')
        return normalized_path

    def parse_request(self, data):
        """Parse the incoming request and extract method, path, and headers."""
        lines = data.decode().splitlines()
        method, path, _ = lines[0].split(' ')
        headers = {line.split(": ")[0]: line.split(": ")[1] for line in lines[1:] if ':' in line}
        return method, path, headers

if __name__ == "__main__":
    HOST, PORT = "localhost", 8080

    socketserver.TCPServer.allow_reuse_address = True
    # Create the server, binding to localhost on port 8080
    server = socketserver.TCPServer((HOST, PORT), MyWebServer)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()
