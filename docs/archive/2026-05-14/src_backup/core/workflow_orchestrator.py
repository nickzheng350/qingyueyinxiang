"""工作流编排器 - 提示词--多维引擎--运行--输出的完整路线"""
import logging
import time
import threading
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Tuple, Union
from enum import Enum
from collections import deque
import uuid

from src.model_dispatcher.type_system import (
    ModelFunctionType, get_consistency_validator, TouchPoint
)
from src.core.unified_engine import (
    UnifiedIntelligentEngine, get_unified_engine,
    TaskPriority, EngineResult
)
from src.core.prompt_engine import (
    DiversifiedPromptEngine, RichPrompt,
    PromptType, QualityLevel
)
from src.core.prompt_awareness import (
    PromptAwarenessEngine, AwarenessResult
)
from src.core.performance import (
    UnifiedPerformanceManager
)

logger = logging.getLogger("hydraflow.core.workflow_orchestrator")


class WorkflowStage(str, Enum):
    """工作流阶段"""
    INPUT = "input"  # 输入阶段
    AWARENESS = "awareness"  # 敏锐性分析阶段
    ENHANCEMENT = "enhancement"  # 提示词增强阶段
    ROUTING = "routing"  # 路由决策阶段
    EXECUTION = "execution"  # 执行阶段
    VALIDATION = "validation"  # 验证阶段
    OUTPUT = "output"  # 输出阶段
    COMPLETED = "completed"  # 完成
    FAILED = "failed"  # 失败


class WorkflowStatus(str, Enum):
    """工作流状态"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class OrchestrationMode(str, Enum):
    """编排模式"""
    AUTO = "auto"  # 全自动
    GUIDED = "guided"  # 引导模式（可干预）
    MANUAL = "manual"  # 手动模式
    CUSTOM = "custom"  # 自定义流程


@dataclass
class StageMetrics:
    """阶段指标"""
    stage: WorkflowStage
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    success: bool = True
    output_size: Optional[int] = None
    error_message: Optional[str] = None


@dataclass
class WorkflowExecution:
    """工作流执行记录"""
    execution_id: str
    workflow_id: str
    stages: List[StageMetrics] = field(default_factory=list)
    status: WorkflowStatus = WorkflowStatus.PENDING
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    final_output: Optional[Any] = None
    total_duration: Optional[float] = None
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


@dataclass
class WorkflowResult:
    """工作流最终结果"""
    success: bool
    execution_id: str
    output: Optional[Any]
    awareness_result: Optional[AwarenessResult]
    metrics: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


@dataclass
class WorkflowConfig:
    """工作流配置"""
    auto_enhance: bool = True
    auto_route: bool = True
    auto_validate: bool = True
    enable_parallel: bool = False
    max_retries: int = 3
    quality_threshold: float = 0.6
    mode: OrchestrationMode = OrchestrationMode.AUTO
    custom_stages: Optional[List[WorkflowStage]] = None


class WorkflowStageProcessor:
    """工作流阶段处理器"""
    
    def __init__(
        self,
        awareness_engine: PromptAwarenessEngine,
        unified_engine: UnifiedIntelligentEngine,
        prompt_engine: DiversifiedPromptEngine,
        perf_manager: UnifiedPerformanceManager,
    ):
        self.awareness_engine = awareness_engine
        self.unified_engine = unified_engine
        self.prompt_engine = prompt_engine
        self.perf_manager = perf_manager
        
        self.consistency_validator = get_consistency_validator()
    
    def process_awareness(
        self,
        prompt: RichPrompt
    ) -> Tuple[AwarenessResult, StageMetrics]:
        """处理敏锐性分析阶段"""
        start_time = time.time()
        
        try:
            awareness_result = self.awareness_engine.analyze(prompt)
            
            end_time = time.time()
            stage_metrics = StageMetrics(
                stage=WorkflowStage.AWARENESS,
                start_time=start_time,
                end_time=end_time,
                duration=end_time - start_time,
                success=True,
            )
            
            return awareness_result, stage_metrics
        except Exception as e:
            end_time = time.time()
            stage_metrics = StageMetrics(
                stage=WorkflowStage.AWARENESS,
                start_time=start_time,
                end_time=end_time,
                duration=end_time - start_time,
                success=False,
                error_message=str(e),
            )
            raise
    
    def process_enhancement(
        self,
        awareness_result: AwarenessResult,
        auto_apply: bool = True
    ) -> Tuple[RichPrompt, StageMetrics]:
        """处理提示词增强阶段"""
        start_time = time.time()
        
        try:
            enhanced_prompt = awareness_result.original_prompt
            
            if auto_apply:
                for suggestion in awareness_result.enhancement_suggestions:
                    if suggestion.expected_improvement > 0.1:
                        suggestion.applied = True
            
            end_time = time.time()
            stage_metrics = StageMetrics(
                stage=WorkflowStage.ENHANCEMENT,
                start_time=start_time,
                end_time=end_time,
                duration=end_time - start_time,
                success=True,
            )
            
            return enhanced_prompt, stage_metrics
        except Exception as e:
            end_time = time.time()
            stage_metrics = StageMetrics(
                stage=WorkflowStage.ENHANCEMENT,
                start_time=start_time,
                end_time=end_time,
                duration=end_time - start_time,
                success=False,
                error_message=str(e),
            )
            raise
    
    def process_routing(
        self,
        awareness_result: AwarenessResult,
        user_preference: Optional[ModelFunctionType] = None
    ) -> Tuple[ModelFunctionType, StageMetrics]:
        """处理路由决策阶段"""
        start_time = time.time()
        
        try:
            recommended = awareness_result.recommended_engines
            
            if user_preference and user_preference in recommended:
                engine_type = user_preference
            elif recommended:
                engine_type = recommended[0]
            else:
                engine_type = ModelFunctionType.TEXT_TO_IMAGE
            
            end_time = time.time()
            stage_metrics = StageMetrics(
                stage=WorkflowStage.ROUTING,
                start_time=start_time,
                end_time=end_time,
                duration=end_time - start_time,
                success=True,
            )
            
            return engine_type, stage_metrics
        except Exception as e:
            end_time = time.time()
            stage_metrics = StageMetrics(
                stage=WorkflowStage.ROUTING,
                start_time=start_time,
                end_time=end_time,
                duration=end_time - start_time,
                success=False,
                error_message=str(e),
            )
            raise
    
    def process_execution(
        self,
        engine_type: ModelFunctionType,
        prompt: RichPrompt,
        priority: TaskPriority = TaskPriority.MEDIUM,
    ) -> Tuple[EngineResult, StageMetrics]:
        """处理执行阶段"""
        start_time = time.time()
        
        try:
            task_id = self.unified_engine.submit_task(
                engine_type,
                prompt,
                priority=priority,
            )
            
            result = None
            max_wait = 30.0
            start_wait = time.time()
            
            while time.time() - start_wait < max_wait:
                result = self.unified_engine.get_task_result(task_id)
                if result:
                    break
                time.sleep(0.1)
            
            if not result:
                result = EngineResult(
                    success=False,
                    task_id=task_id,
                    errors=["Task execution timeout"],
                )
            
            end_time = time.time()
            stage_metrics = StageMetrics(
                stage=WorkflowStage.EXECUTION,
                start_time=start_time,
                end_time=end_time,
                duration=end_time - start_time,
                success=result.success,
                error_message="; ".join(result.errors) if result.errors else None,
            )
            
            return result, stage_metrics
        except Exception as e:
            end_time = time.time()
            stage_metrics = StageMetrics(
                stage=WorkflowStage.EXECUTION,
                start_time=start_time,
                end_time=end_time,
                duration=end_time - start_time,
                success=False,
                error_message=str(e),
            )
            raise
    
    def process_validation(
        self,
        result: EngineResult,
        engine_type: ModelFunctionType,
    ) -> Tuple[bool, StageMetrics]:
        """处理验证阶段"""
        start_time = time.time()
        
        try:
            is_valid = self.consistency_validator.validate(
                engine_type,
                {"has_output": result.output is not None, "success": result.success},
                TouchPoint.PRE_PROCESSING,
            )
            
            if isinstance(is_valid, tuple):
                is_valid = is_valid[0]
            
            end_time = time.time()
            stage_metrics = StageMetrics(
                stage=WorkflowStage.VALIDATION,
                start_time=start_time,
                end_time=end_time,
                duration=end_time - start_time,
                success=is_valid,
            )
            
            return is_valid, stage_metrics
        except Exception as e:
            end_time = time.time()
            stage_metrics = StageMetrics(
                stage=WorkflowStage.VALIDATION,
                start_time=start_time,
                end_time=end_time,
                duration=end_time - start_time,
                success=False,
                error_message=str(e),
            )
            raise
    
    def process_output(
        self,
        result: EngineResult,
        awareness_result: AwarenessResult,
    ) -> Tuple[Any, StageMetrics]:
        """处理输出阶段"""
        start_time = time.time()
        
        try:
            output = result.output
            
            end_time = time.time()
            stage_metrics = StageMetrics(
                stage=WorkflowStage.OUTPUT,
                start_time=start_time,
                end_time=end_time,
                duration=end_time - start_time,
                success=True,
            )
            
            return output, stage_metrics
        except Exception as e:
            end_time = time.time()
            stage_metrics = StageMetrics(
                stage=WorkflowStage.OUTPUT,
                start_time=start_time,
                end_time=end_time,
                duration=end_time - start_time,
                success=False,
                error_message=str(e),
            )
            raise


class WorkflowOrchestrator:
    """工作流编排器 - 统一核心"""
    
    _instance: Optional["WorkflowOrchestrator"] = None
    _initialized: bool = False
    
    def __new__(cls) -> "WorkflowOrchestrator":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        self.unified_engine = get_unified_engine()
        self.prompt_engine = DiversifiedPromptEngine()
        self.awareness_engine = PromptAwarenessEngine()
        self.perf_manager = UnifiedPerformanceManager()
        
        self.stage_processor = WorkflowStageProcessor(
            self.awareness_engine,
            self.unified_engine,
            self.prompt_engine,
            self.perf_manager,
        )
        
        self.executions: Dict[str, WorkflowExecution] = {}
        self.execution_queue: deque = deque()
        self.active_execution: Optional[WorkflowExecution] = None
        
        self.lock = threading.RLock()
        self.running = False
        self.work_thread: Optional[threading.Thread] = None
        
        logger.info("WorkflowOrchestrator initialized")
    
    def create_workflow(
        self,
        prompt: Union[str, RichPrompt],
        prompt_type: PromptType = PromptType.TEXT,
        quality: QualityLevel = QualityLevel.STANDARD,
        config: Optional[WorkflowConfig] = None,
    ) -> str:
        """创建工作流"""
        workflow_id = str(uuid.uuid4())
        
        if isinstance(prompt, str):
            rich_prompt = self.prompt_engine.create_prompt(
                prompt_type,
                prompt,
                quality=quality,
            )
        else:
            rich_prompt = prompt
        
        execution = WorkflowExecution(
            execution_id=str(uuid.uuid4()),
            workflow_id=workflow_id,
            status=WorkflowStatus.PENDING,
        )
        
        execution.context = {
            "prompt": rich_prompt,
            "config": config or WorkflowConfig(),
            "quality": quality,
        }
        
        with self.lock:
            self.executions[execution.execution_id] = execution
            self.execution_queue.append(execution.execution_id)
        
        return execution.execution_id
    
    def execute_workflow(
        self,
        execution_id: str,
        priority: TaskPriority = TaskPriority.MEDIUM,
    ) -> WorkflowResult:
        """执行工作流 - 完整路线: 提示词--多维引擎--运行--输出"""
        execution = self.executions.get(execution_id)
        if not execution:
            raise ValueError(f"Execution not found: {execution_id}")
        
        with self.lock:
            execution.status = WorkflowStatus.RUNNING
        
        rich_prompt = execution.context["prompt"]
        config = execution.context.get("config", WorkflowConfig())
        
        awareness_result = None
        final_output = None
        final_success = False
        warnings = []
        errors = []
        
        try:
            stage = WorkflowStage.INPUT
            input_metrics = StageMetrics(
                stage=stage,
                start_time=time.time(),
                end_time=time.time(),
                duration=0.0,
                success=True,
            )
            execution.stages.append(input_metrics)
            
            stage = WorkflowStage.AWARENESS
            awareness_result, awareness_metrics = self.stage_processor.process_awareness(
                rich_prompt
            )
            execution.stages.append(awareness_metrics)
            
            if config.auto_enhance:
                stage = WorkflowStage.ENHANCEMENT
                enhanced_prompt, enhance_metrics = self.stage_processor.process_enhancement(
                    awareness_result, auto_apply=True
                )
                execution.stages.append(enhance_metrics)
                rich_prompt = enhanced_prompt
            
            stage = WorkflowStage.ROUTING
            engine_type, routing_metrics = self.stage_processor.process_routing(
                awareness_result
            )
            execution.stages.append(routing_metrics)
            
            stage = WorkflowStage.EXECUTION
            engine_result, exec_metrics = self.stage_processor.process_execution(
                engine_type, rich_prompt, priority
            )
            execution.stages.append(exec_metrics)
            
            if config.auto_validate:
                stage = WorkflowStage.VALIDATION
                is_valid, validation_metrics = self.stage_processor.process_validation(
                    engine_result, engine_type
                )
                execution.stages.append(validation_metrics)
                
                if not is_valid:
                    warnings.append("Output validation warning")
            
            stage = WorkflowStage.OUTPUT
            final_output, output_metrics = self.stage_processor.process_output(
                engine_result, awareness_result
            )
            execution.stages.append(output_metrics)
            
            final_success = True
            stage = WorkflowStage.COMPLETED
            
        except Exception as e:
            final_success = False
            errors.append(str(e))
            stage = WorkflowStage.FAILED
        
        with self.lock:
            execution.status = WorkflowStatus.COMPLETED if final_success else WorkflowStatus.FAILED
            execution.end_time = time.time()
            execution.total_duration = execution.end_time - execution.start_time
            execution.final_output = final_output
            execution.warnings = warnings
            execution.errors = errors
        
        return WorkflowResult(
            success=final_success,
            execution_id=execution_id,
            output=final_output,
            awareness_result=awareness_result,
            metrics={
                "total_duration": execution.total_duration,
                "stages": len(execution.stages),
            },
            warnings=warnings,
            errors=errors,
        )
    
    def quick_process(
        self,
        prompt: Union[str, RichPrompt],
        prompt_type: PromptType = PromptType.IMAGE,
        quality: QualityLevel = QualityLevel.STANDARD,
        priority: TaskPriority = TaskPriority.MEDIUM,
    ) -> WorkflowResult:
        """快速处理 - 一键完整路线"""
        execution_id = self.create_workflow(prompt, prompt_type, quality)
        return self.execute_workflow(execution_id, priority)
    
    def start_services(self):
        """启动所有服务"""
        self.unified_engine.start()
        self.perf_manager.start()
        self.running = True
    
    def stop_services(self):
        """停止所有服务"""
        self.running = False
        self.unified_engine.stop()
        self.perf_manager.stop()
    
    def get_execution_status(self, execution_id: str) -> Optional[WorkflowExecution]:
        """获取执行状态"""
        return self.executions.get(execution_id)
    
    def get_system_summary(self) -> Dict[str, Any]:
        """获取系统总结"""
        completed = sum(
            1 for exec in self.executions.values()
            if exec.status == WorkflowStatus.COMPLETED
        )
        failed = sum(
            1 for exec in self.executions.values()
            if exec.status == WorkflowStatus.FAILED
        )
        pending = sum(
            1 for exec in self.executions.values()
            if exec.status == WorkflowStatus.PENDING
        )
        
        return {
            "total_executions": len(self.executions),
            "completed": completed,
            "failed": failed,
            "pending": pending,
            "engine_status": self.unified_engine.get_system_status(),
        }


def get_workflow_orchestrator() -> WorkflowOrchestrator:
    """获取工作流编排器单例"""
    return WorkflowOrchestrator()
