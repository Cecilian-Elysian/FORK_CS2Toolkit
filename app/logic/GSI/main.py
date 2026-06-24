from http.server import BaseHTTPRequestHandler, HTTPServer
import json

class GSIHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data_bytes = self.rfile.read(content_length)
            
            post_data = None
            for encoding in ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']:
                try:
                    post_data = post_data_bytes.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            
            if post_data is None:
                post_data = post_data_bytes.decode('utf-8', errors='ignore')
            
            game_state = json.loads(post_data)

            print("接收到 GSI 信息:")
            print(json.dumps(game_state, indent=4))

            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"OK")
        except Exception as e:
            print(f"处理POST请求时出错: {e}")
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b"Error processing GSI data")


def run_server(port=3000):
    server_address = ('127.0.0.1', port)
    httpd = HTTPServer(server_address, GSIHandler)
    print(f"监听服务已开启于端口{port}...")
    httpd.serve_forever()


if __name__ == '__main__':
    run_server()