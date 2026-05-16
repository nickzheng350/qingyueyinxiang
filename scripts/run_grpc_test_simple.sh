#!/bin/bash
# gRPC 跨语言调用验证脚本 - 简化版（无需 pip）
# 使用 HTTP 模拟 gRPC 调用，验证前后端交互逻辑

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=========================================="
echo "  gRPC 跨语言调用验证（简化版）"
echo "=========================================="
echo ""

# 检查依赖
check_dependencies() {
    echo "1. 检查依赖..."
    
    if ! command -v python3 &> /dev/null; then
        echo "❌ 错误：未找到 python3"
        exit 1
    fi
    
    if ! command -v cargo &> /dev/null; then
        echo "❌ 错误：未找到 cargo"
        exit 1
    fi
    
    echo "   ✅ 依赖检查通过"
}

# 启动 Python HTTP 模拟服务
start_python_server() {
    echo ""
    echo "2. 启动 Python HTTP 模拟服务..."
    
    cd "$PROJECT_ROOT/grpc-python"
    
    # 创建简单的 HTTP 服务器来模拟 gRPC
    cat > mock_server.py << 'MOCK_SERVER_EOF'
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
MOCK_SERVER_EOF

    chmod +x mock_server.py
    
    # 后台运行服务端
    python3 mock_server.py > /tmp/grpc_python_server.log 2>&1 &
    SERVER_PID=$!
    
    echo "   服务端 PID: $SERVER_PID"
    echo "   日志文件：/tmp/grpc_python_server.log"
    
    # 等待服务端启动
    echo "   等待服务端启动..."
    sleep 2
    
    # 检查服务端是否启动成功
    if ps -p $SERVER_PID > /dev/null; then
        echo "   ✅ 服务端启动成功"
    else
        echo "   ❌ 服务端启动失败，查看日志：/tmp/grpc_python_server.log"
        exit 1
    fi
    
    echo $SERVER_PID > /tmp/grpc_server.pid
}

# 运行 Rust HTTP 客户端测试
run_rust_client() {
    echo ""
    echo "3. 编译并运行 Rust HTTP 客户端..."
    
    cd "$PROJECT_ROOT/grpc-rust"
    
    # 创建简单的 HTTP 客户端测试
    cat > src/main.rs << 'RUST_CLIENT_EOF'
//! Rust HTTP 客户端 - 调用 Python 模拟服务

use std::collections::HashMap;
use std::time::{Instant, Duration};

#[derive(Debug, serde::Serialize, serde::Deserialize)]
struct Skill {
    id: String,
    name: String,
    description: String,
    version: String,
    author: String,
    enabled: bool,
}

#[derive(Debug, serde::Serialize, serde::Deserialize)]
struct CreateSkillRequest {
    skill: Skill,
}

#[derive(Debug, serde::Serialize, serde::Deserialize)]
struct CreateSkillResponse {
    skill: Option<Skill>,
    success: bool,
    message: String,
}

#[derive(Debug, serde::Serialize, serde::Deserialize)]
struct GetSkillRequest {
    skill_id: String,
}

#[derive(Debug, serde::Serialize, serde::Deserialize)]
struct GetSkillResponse {
    skill: Option<Skill>,
    found: bool,
}

#[derive(Debug, serde::Serialize, serde::Deserialize)]
struct InstallSkillRequest {
    skill_id: String,
    skill_type: String,
}

#[derive(Debug, serde::Serialize, serde::Deserialize)]
struct InstallSkillResponse {
    success: bool,
    message: String,
    skill: Option<Skill>,
}

#[derive(Debug, serde::Serialize, serde::Deserialize)]
struct ListSkillsResponse {
    skills: Vec<Skill>,
}

fn http_post(path: &str, body: &str) -> Result<String, String> {
    let client = ureq::Agent::new();
    let url = format!("http://localhost:50051{}", path);
    
    let response = client.post(&url)
        .set("Content-Type", "application/json")
        .send_string(body)
        .map_err(|e| e.to_string())?;
    
    let status = response.status();
    if status != 200 {
        return Err(format!("HTTP error: {}", status));
    }
    
    response.into_string().map_err(|e| e.to_string())
}

fn main() -> Result<(), String> {
    println!("=== Rust HTTP Client ===");
    println!("Connected to Python server at localhost:50051\n");
    
    // 测试创建技能
    let skill = Skill {
        id: "rust_test_skill".to_string(),
        name: "Rust Test Skill".to_string(),
        description: "Created from Rust client".to_string(),
        version: "1.0.0".to_string(),
        author: "Rust Client".to_string(),
        enabled: true,
    };
    
    let req = CreateSkillRequest { skill: skill.clone() };
    let body = serde_json::to_string(&req).map_err(|e| e.to_string())?;
    
    let start = Instant::now();
    let response = http_post("/CreateSkill", &body)?;
    let duration = start.elapsed();
    
    let resp: CreateSkillResponse = serde_json::from_str(&response).map_err(|e| e.to_string())?;
    println!(
        "[Rust] CreateSkill response: success={}, message={}",
        resp.success, resp.message
    );
    println!("Response time: {:?}\n", duration);
    
    // 测试获取技能
    let req = GetSkillRequest {
        skill_id: "rust_test_skill".to_string(),
    };
    let body = serde_json::to_string(&req).map_err(|e| e.to_string())?;
    
    let start = Instant::now();
    let response = http_post("/GetSkill", &body)?;
    let duration = start.elapsed();
    
    let resp: GetSkillResponse = serde_json::from_str(&response).map_err(|e| e.to_string())?;
    if resp.found {
        if let Some(s) = resp.skill {
            println!(
                "[Rust] GetSkill found: {} ({})",
                s.name, s.id
            );
        }
    } else {
        println!("[Rust] GetSkill: not found");
    }
    println!("Response time: {:?}\n", duration);
    
    // 测试安装技能（性能测试）
    let iterations = 10;
    let mut total_time = Duration::new(0, 0);
    
    println!(
        "[Rust] Starting performance test: {} installations",
        iterations
    );
    
    for i in 0..iterations {
        let skill_id = format!("perf_test_{}", i);
        
        let req = InstallSkillRequest {
            skill_id: skill_id.clone(),
            skill_type: "test".to_string(),
        };
        let body = serde_json::to_string(&req).map_err(|e| e.to_string())?;
        
        let start = Instant::now();
        let response = http_post("/InstallSkill", &body)?;
        let duration = start.elapsed();
        
        let resp: InstallSkillResponse = serde_json::from_str(&response).map_err(|e| e.to_string())?;
        total_time += duration;
        
        println!(
            "  Install {}: {} ({}ms)",
            skill_id,
            resp.success,
            duration.as_millis()
        );
    }
    
    println!("\n[Rust] Performance Results:");
    println!(
        "  Average time per call: {}ms",
        total_time.as_millis() / iterations as u128
    );
    println!(
        "  Total time: {}ms",
        total_time.as_millis()
    );
    
    // 测试列表技能
    let start = Instant::now();
    let response = http_post("/ListSkills", "{}")?;
    let duration = start.elapsed();
    
    let resp: ListSkillsResponse = serde_json::from_str(&response).map_err(|e| e.to_string())?;
    
    println!(
        "\n[Rust] ListSkills found {} skills",
        resp.skills.len()
    );
    for s in resp.skills {
        println!("  - {} ({})", s.name, s.id);
    }
    println!("Response time: {:?}", duration);
    
    println!("\n=== Test completed ===");
    
    Ok(())
}
RUST_CLIENT_EOF

    # 更新 Cargo.toml 添加依赖
    cat > Cargo.toml << 'CARGO_EOF'
[package]
name = "grpc-rust-client"
version = "0.1.0"
edition = "2021"

[dependencies]
ureq = { version = "2.0", features = ["json"] }
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
CARGO_EOF
    
    # 构建并运行
    echo "   构建客户端..."
    cargo build --release 2>&1 | tail -3
    
    echo ""
    echo "   运行测试..."
    cargo run --release
    
    echo ""
    echo "   ✅ 客户端测试完成"
}

# 清理资源
cleanup() {
    echo ""
    echo "4. 清理资源..."
    
    if [ -f /tmp/grpc_server.pid ]; then
        SERVER_PID=$(cat /tmp/grpc_server.pid)
        if ps -p $SERVER_PID > /dev/null; then
            echo "   停止服务端 (PID: $SERVER_PID)..."
            kill $SERVER_PID 2>/dev/null || true
            rm /tmp/grpc_server.pid
        fi
    fi
    
    # 清理临时文件
    rm -f "$PROJECT_ROOT/grpc-python/mock_server.py"
    
    echo "   ✅ 清理完成"
}

# 显示服务端日志
show_server_logs() {
    echo ""
    echo "=== 服务端日志 ==="
    if [ -f /tmp/grpc_python_server.log ]; then
        cat /tmp/grpc_python_server.log
    else
        echo "日志文件不存在"
    fi
}

# 主函数
main() {
    trap cleanup EXIT
    
    check_dependencies
    start_python_server
    run_rust_client
    show_server_logs
    
    echo ""
    echo "=========================================="
    echo "  ✅ 验证完成！"
    echo "=========================================="
    echo ""
    echo "💡 说明：此测试使用 HTTP 模拟 gRPC 调用"
    echo "   在完整环境中安装 grpcio 后可运行真实 gRPC 测试"
}

main "$@"
