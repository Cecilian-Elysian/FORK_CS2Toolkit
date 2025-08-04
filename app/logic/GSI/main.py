from http.server import BaseHTTPRequestHandler, HTTPServer
import json

class GSIHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        game_state = json.loads(post_data)

        print("Received GSI data:")
        print(json.dumps(game_state, indent=4))

        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"OK")


def run_server(port=3000):
    server_address = ('127.0.0.1', port)
    httpd = HTTPServer(server_address, GSIHandler)
    print(f"Starting GSI server on port {port}...")
    httpd.serve_forever()


if __name__ == '__main__':
    run_server()