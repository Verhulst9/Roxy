"""
Simple HTTP API Server for Nakari Desktop Pet
使用 Python 内置 http.server，无需额外依赖
"""
import http.server
import socketserver
import json
import sys
from urllib.parse import urlparse, parse_qs

# Port
PORT = 8000


class NakariAPIHandler(http.server.BaseHTTPRequestHandler):
    """处理 API 请求"""

    def _send_json_response(self, data, status=200):
        """发送 JSON 响应"""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        response = json.dumps(data, ensure_ascii=False)
        self.wfile.write(response.encode('utf-8'))

    def _send_cors_headers(self):
        """处理 CORS 预检请求"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_OPTIONS(self):
        """处理 OPTIONS 预检请求"""
        self._send_cors_headers()

    def do_GET(self):
        """处理 GET 请求"""
        parsed_path = urlparse(self.path)

        if parsed_path.path == '/':
            self._send_json_response({
                "message": "Nakari Simple API Server",
                "version": "1.0.0-simple"
            })
        elif parsed_path.path == '/api/status':
            self._send_json_response({
                "status": "online",
                "is_reflecting": False,
                "active_sessions": 0
            })
        else:
            self._send_json_response({"error": "Not found"}, 404)

    def do_POST(self):
        """处理 POST 请求"""
        parsed_path = urlparse(self.path)

        if parsed_path.path == '/api/chat':
            # 读取请求体
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)

            try:
                data = json.loads(post_data.decode('utf-8'))
                message = data.get('message', '')
                session_id = data.get('session_id', 'desktop_pet')

                print(f"[API] Chat from {session_id}: {message}")

                # 简单的回复逻辑（可替换为真实的 LLM 调用）
                response_text = self._generate_response(message)

                self._send_json_response({
                    "response": response_text,
                    "session_id": session_id,
                    "timestamp": "2025-01-13T12:00:00",
                    "is_thinking": False
                })

            except json.JSONDecodeError:
                self._send_json_response({"error": "Invalid JSON"}, 400)
            except Exception as e:
                print(f"[API] Error: {e}")
                self._send_json_response({"error": str(e)}, 500)
        else:
            self._send_json_response({"error": "Not found"}, 404)

    def _generate_response(self, message):
        """生成回复（简单实现）"""
        message_lower = message.lower()

        # 简单的关键词匹配回复
        if any(word in message_lower for word in ['你好', 'hello', 'hi']):
            return "你好！我是 Nakari，很高兴见到你！"
        elif any(word in message_lower for word in ['名字', 'name', '是谁']):
            return "我是 Nakari，你的桌面伙伴！"
        elif any(word in message_lower for word in ['谢谢', 'thank']):
            return "不客气！很高兴能帮到你~"
        elif any(word in message_lower for word in ['再见', 'bye']):
            return "再见！有空再来聊天吧~"
        elif any(word in message_lower for word in ['开心', '高兴', 'happy']):
            return "看到你开心我也很开心！"
        elif any(word in message_lower for word in ['难过', '伤心', 'sad']):
            return "别难过，一切都会好起来的！"
        elif '?' in message or '？' in message or '怎么' in message or '如何' in message or '什么' in message:
            return f"关于「{message}」这个问题，让我想想...这是个好问题！"
        else:
            responses = [
                f"你说「{message}」很有意思呢！",
                "嗯嗯，我明白你的意思。",
                "继续说，我在认真听呢~",
                "这让我想到很多有趣的事情！",
                "哈哈，你真有趣！"
            ]
            import random
            return random.choice(responses)

    def log_message(self, format, *args):
        """覆盖默认的日志输出"""
        pass  # 静默模式


def start_server():
    """启动 API Server"""
    with socketserver.TCPServer(("", PORT), NakariAPIHandler) as httpd:
        print(f"[API] Simple API Server started on http://localhost:{PORT}")
        print(f"[API] Chat endpoint: http://localhost:{PORT}/api/chat")
        print(f"[API] Press Ctrl+C to stop")

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[API] Server stopped")
            httpd.shutdown()


if __name__ == "__main__":
    start_server()
