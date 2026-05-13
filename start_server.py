"""简单的静态文件服务器"""

import http.server
import socketserver
import os
import sys

PORT = 9090

def main():
    # 切换到UI目录
    ui_dir = os.path.join(os.path.dirname(__file__), 'ui', 'public')
    os.chdir(ui_dir)
    
    # 创建请求处理器
    Handler = http.server.SimpleHTTPRequestHandler
    
    # 设置端口
    socketserver.TCPServer.allow_reuse_address = True
    
    try:
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            print(f"🚀 HydraFlow AI 服务器启动成功！")
            print(f"📍 访问地址: http://localhost:{PORT}")
            print(f"📁 服务目录: {os.getcwd()}")
            print(f"\n按 Ctrl+C 停止服务器")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
        sys.exit(0)
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"❌ 端口 {PORT} 已被占用，请使用其他端口")
            sys.exit(1)
        else:
            raise

if __name__ == "__main__":
    main()
