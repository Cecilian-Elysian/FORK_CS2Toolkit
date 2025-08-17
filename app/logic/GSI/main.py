from http.server import BaseHTTPRequestHandler, HTTPServer
import json

class GSIHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data_bytes = self.rfile.read(content_length)
            
            # 尝试多种编码方式解码数据
            post_data = None
            for encoding in ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']:
                try:
                    post_data = post_data_bytes.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            
            if post_data is None:
                # 如果所有编码都失败，使用错误处理方式
                post_data = post_data_bytes.decode('utf-8', errors='ignore')
                print("警告: GSI数据包含无法解码的字符，已忽略部分内容")
            
            game_state = json.loads(post_data)

            print("Received GSI data:")
            print(json.dumps(game_state, indent=4))

            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"OK")
        except Exception as e:
            print(f"处理GSI POST请求时出错: {e}")
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b"Error processing GSI data")


def run_server(port=3000):
    server_address = ('127.0.0.1', port)
    httpd = HTTPServer(server_address, GSIHandler)
    print(f"Starting GSI server on port {port}...")
    httpd.serve_forever()


if __name__ == '__main__':
    run_server()