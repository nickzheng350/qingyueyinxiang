#!/usr/bin/env python3
"""
HTTP 模拟 gRPC 服务 - 技能管理服务
无需 grpc 模块，使用简单的 HTTP POST 请求模拟
"""

import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

skills = {}
lock = threading.Lock()

class SkillServiceHandler(BaseHTTPRequestHandler):
    def _send_response(self, status_code, data):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length).decode()
        data = json.loads(body) if body else {}
        
        print(f"[Python] 接收到请求: {self.path}")
        
        if self.path == '/CreateSkill':
            self.handle_create_skill(data)
        elif self.path == '/GetSkill':
            self.handle_get_skill(data)
        elif self.path == '/ListSkills':
            self.handle_list_skills(data)
        elif self.path == '/InstallSkill':
            self.handle_install_skill(data)
        else:
            self._send_response(404, {'error': 'Not found'})
    
    def handle_create_skill(self, data):
        skill = data.get('skill', {})
        skill_id = skill.get('id', '')
        
        with lock:
            if skill_id in skills:
                self._send_response(200, {
                    'success': False,
                    'message': f'Skill {skill_id} already exists'
                })
                return
            
            skills[skill_id] = skill
        
        self._send_response(200, {
            'skill': skill,
            'success': True,
            'message': 'Skill created successfully'
        })
        print(f"[Python] 创建技能成功: {skill_id}")
    
    def handle_get_skill(self, data):
        skill_id = data.get('skill_id', '')
        
        with lock:
            skill = skills.get(skill_id)
        
        if skill:
            self._send_response(200, {'skill': skill, 'found': True})
            print(f"[Python] 获取技能: {skill_id}")
        else:
            self._send_response(200, {'found': False})
            print(f"[Python] 技能不存在: {skill_id}")
    
    def handle_list_skills(self, data):
        with lock:
            skill_list = list(skills.values())
        
        self._send_response(200, {'skills': skill_list})
        print(f"[Python] 列出技能: {len(skill_list)} 个")
    
    def handle_install_skill(self, data):
        import time
        
        skill_id = data.get('skill_id', '')
        print(f"[Python] 开始安装技能: {skill_id}")
        
        # 模拟下载和安装延迟
        time.sleep(0.2)
        
        skill = {
            'id': skill_id,
            'name': f'Skill {skill_id}',
            'description': 'Installed via HTTP',
            'version': '1.0.0',
            'author': 'HTTP Mock',
            'enabled': True
        }
        
        with lock:
            skills[skill_id] = skill
        
        print(f"[Python] 技能安装完成: {skill_id}")
        
        self._send_response(200, {
            'success': True,
            'message': f'Skill {skill_id} installed',
            'skill': skill
        })
    
    def log_message(self, format, *args):
        # 禁用默认日志
        pass

def run_server():
    server = HTTPServer(('localhost', 50051), SkillServiceHandler)
    print("[Python] HTTP 模拟服务已启动 (端口 50051)")
    server.serve_forever()

if __name__ == '__main__':
    run_server()
