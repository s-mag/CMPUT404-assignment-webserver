import os
import socket

ROOT_DIRECTORY = 'www'

# Mapping file extensions to their MIME types
MIME_TYPES = {
    '.html': 'text/html',
    '.css': 'text/css'
}

# Mapping HTTP status codes to their reason phrases
CODES = {
    404: 'Not Found',
    200: 'OK',
    405: 'Method Not Allowed',
    301: 'Moved Permanently',
    400: 'Bad Request'
}

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("localhost", 8080)) 
    server_socket.listen(10)
    
    print("Server started on port 8080")
    
    while True:
        client_conn, client_addr = server_socket.accept()
        handle_request(client_conn)

def handle_request(connection):
    request_data = connection.recv(1024).decode().strip()
    
    if not request_data:
        connection.close()
        return
    
    request_method, request_path, _ = parse_request(request_data)
    
    if request_method.upper() != 'GET':
        send_response(connection, 405)
        return
    
    resolved_path = get_path(request_path)
    
    # Redirect to directory with a trailing slash if needed
    if os.path.isdir(resolved_path) and not request_path.endswith('/'):
        redirect(connection, request_path)
        return
    
    # Send a 404 error if the file does not exist
    if not os.path.isfile(resolved_path):
        send_response(connection, 404)
        return

    with open(resolved_path, 'rb') as file_content:
        content_data = file_content.read()
        send_response(connection, 200, content_data, os.path.splitext(resolved_path)[1])

    connection.close()

def send_response(connection, status_code, content_data=None, file_extension='.html'):
    # Generate error pages for non-200 status codes
    if status_code != 200:
        content_data = f"<html><body><h1>{status_code} {CODES[status_code]}</h1></body></html>".encode()
    
    # Prepare the HTTP headers for the response
    headers = {
        "Content-Type": MIME_TYPES.get(file_extension, 'text/plain'),
        "Content-Length": str(len(content_data)),
        "Connection": "close"
    }
    
    # Construct the HTTP response and send it to the client
    response = f"HTTP/1.1 {status_code} {CODES[status_code]}\r\n"
    headers_str = ''.join([f"{header_name}: {header_value}\r\n" for header_name, header_value in headers.items()])
    connection.sendall(f"{response}{headers_str}\r\n".encode() + content_data)

def redirect(connection, path):
    headers = {
        "Location": path + '/'
    }
    response = f"HTTP/1.1 301 {CODES[301]}\r\n"
    headers_str = ''.join([f"{header_name}: {header_value}\r\n" for header_name, header_value in headers.items()])
    connection.sendall(f"{response}{headers_str}\r\n".encode())

def get_path(path):
    # Normalize the path to prevent directory traversal attacks
    normalized_path = os.path.normpath(ROOT_DIRECTORY + path)
    
    # Serve the index.html file if the request is for a directory
    if os.path.isdir(normalized_path) and path.endswith('/'):
        return os.path.join(normalized_path, 'index.html')

    return normalized_path

def parse_request(data):
    request_lines = data.splitlines()
    
    # Extract the method, path, and protocol from the request line
    method, path, protocol = request_lines[0].split(' ')
    
    # Extract the headers from the rest of the request
    headers = {}
    for line in request_lines[1:]:
        if ':' in line:
            header_name, header_value = line.split(': ', 1)
            headers[header_name] = header_value
            
    return method, path, headers

if __name__ == "__main__":
    main()
