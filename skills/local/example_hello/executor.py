"""Hello World 示例技能执行器"""

from src.skills.skill_engine import SkillExecutor, SkillExecutionResult, SkillContext


class HelloSkillExecutor(SkillExecutor):
    """Hello World 技能执行器"""
    
    async def execute(self, name: str = "World", greeting: str = None) -> SkillExecutionResult:
        """
        执行 Hello World 技能
        
        参数:
            name: 要问候的名字
            greeting: 问候语（可选，默认使用配置中的 default_greeting）
        
        返回:
            SkillExecutionResult: 执行结果
        """
        try:
            # 从配置中获取默认问候语
            default_greeting = self.context.config.get("default_greeting", "Hello")
            actual_greeting = greeting or default_greeting
            
            # 生成问候语
            message = f"{actual_greeting}, {name}!"
            
            # 如果启用了日志，记录执行信息
            if self.context.config.get("enable_logging", True):
                print(f"[HelloSkill] 执行问候：{message}")
            
            return SkillExecutionResult(
                success=True,
                data={
                    "message": message,
                    "name": name,
                    "greeting": actual_greeting,
                    "skill_info": {
                        "id": self.context.skill_id,
                        "name": self.context.skill_name,
                        "version": self.context.skill_version,
                    }
                },
                metadata={
                    "executor": "HelloSkillExecutor",
                    "context_config": self.context.config,
                }
            )
            
        except Exception as e:
            return SkillExecutionResult(
                success=False,
                error=str(e),
                metadata={"executor": "HelloSkillExecutor"}
            )
    
    def execute_sync(self, name: str = "World", greeting: str = None) -> SkillExecutionResult:
        """同步执行（直接调用异步版本）"""
        import asyncio
        return asyncio.run(self.execute(name=name, greeting=greeting))
