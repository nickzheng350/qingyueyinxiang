#!/usr/bin/env python3
"""
Python gRPC 服务端 - 技能管理服务
用于演示 Rust 客户端如何调用 Python API
"""

import grpc
import time
import threading
from concurrent import futures

# 生成的 protobuf 模块
import skill_pb2
import skill_pb2_grpc

class SkillService(skill_pb2_grpc.SkillServiceServicer):
    """技能服务实现"""
    
    def __init__(self):
        self.skills = {}
        self.lock = threading.Lock()
    
    def CreateSkill(self, request, context):
        """创建技能"""
        skill = request.skill
        
        with self.lock:
            if skill.id in self.skills:
                return skill_pb2.CreateSkillResponse(
                    success=False,
                    message=f"Skill {skill.id} already exists"
                )
            
            self.skills[skill.id] = skill
        
        return skill_pb2.CreateSkillResponse(
            skill=skill,
            success=True,
            message="Skill created successfully"
        )
    
    def GetSkill(self, request, context):
        """获取技能"""
        with self.lock:
            skill = self.skills.get(request.skill_id)
        
        if skill:
            return skill_pb2.GetSkillResponse(
                skill=skill,
                found=True
            )
        
        return skill_pb2.GetSkillResponse(
            found=False
        )
    
    def ListSkills(self, request, context):
        """列出所有技能"""
        with self.lock:
            skills = list(self.skills.values())
        
        return skill_pb2.ListSkillsResponse(skills=skills)
    
    def InstallSkill(self, request, context):
        """安装技能（模拟耗时操作）"""
        import time
        
        # 模拟下载和安装过程
        print(f"[Python] Starting installation of skill: {request.skill_id}")
        time.sleep(0.5)  # 模拟网络延迟
        
        with self.lock:
            # 创建技能记录
            skill = skill_pb2.Skill(
                id=request.skill_id,
                name=f"Skill {request.skill_id}",
                description=f"Installed via gRPC",
                version="1.0.0",
                author="gRPC",
                enabled=True
            )
            self.skills[request.skill_id] = skill
        
        print(f"[Python] Skill {request.skill_id} installed successfully")
        
        return skill_pb2.InstallSkillResponse(
            success=True,
            message=f"Skill {request.skill_id} installed",
            skill=skill
        )

def serve():
    """启动 gRPC 服务"""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    skill_pb2_grpc.add_SkillServiceServicer_to_server(SkillService(), server)
    
    server.add_insecure_port('[::]:50051')
    server.start()
    print("[Python] gRPC server started on port 50051")
    
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == '__main__':
    serve()