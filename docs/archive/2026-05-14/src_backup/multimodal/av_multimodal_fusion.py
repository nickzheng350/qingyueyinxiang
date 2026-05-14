"""音视频多模态融合引擎 - 电影级音视频融合与独立生成能力"""
import logging
import time
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum
from abc import ABC, abstractmethod

from src.model_dispatcher.type_system import (
    ModelFunctionType,
    get_consistency_validator,
    TouchPoint,
)
from src.multimodal.audio_prompt_engine import AudioPromptEngine, MusicalGenre
from src.multimodal.enhanced_audio_engine import (
    EnhancedAudioEngine,
    ProjectStyleGuide,
    ScriptParseResult,
)
from src.multimodal.image_to_video import ImageToVideoGenerator
from src.multimodal.style_transfer import StyleTransferEngine
from src.multimodal.format_converter import FormatConverter

logger = logging.getLogger("hydraflow.multimodal.av_fusion")


class ProductionQuality(str, Enum):
    """制作质量等级"""
    WEB = "web"
    BROADCAST = "broadcast"
    CINEMATIC = "cinematic"
    DOLBY_VISION = "dolby_vision"
    IMAX = "imax"


class OutputFormat(str, Enum):
    """输出格式"""
    MP4_H264 = "mp4_h264"
    MP4_H265 = "mp4_h265"
    MOV_PRORES = "mov_prores"
    MKV = "mkv"
    DCP = "dcp"


class AudioConfig(str, Enum):
    """音频配置"""
    STEREO = "stereo"
    SURROUND_5_1 = "surround_5_1"
    SURROUND_7_1 = "surround_7_1"
    IMMERSIVE_ATMOS = "immersive_atmos"


@dataclass
class ProductionSettings:
    """制作设置"""
    quality: ProductionQuality = ProductionQuality.CINEMATIC
    output_format: OutputFormat = OutputFormat.MP4_H264
    audio_config: AudioConfig = AudioConfig.SURROUND_5_1
    resolution: tuple = (1920, 1080)
    fps: float = 24.0
    bitrate_video: str = "20M"
    bitrate_audio: str = "320k"
    color_space: str = "Rec.709"
    aspect_ratio: str = "16:9"
    output_path: Optional[str] = None


@dataclass
class Asset:
    """资产"""
    asset_id: str
    asset_type: str
    path: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VideoAsset(Asset):
    """视频资产"""
    duration: float = 0.0
    fps: float = 24.0
    resolution: tuple = (1920, 1080)


@dataclass
class AudioAsset(Asset):
    """音频资产"""
    duration: float = 0.0
    sample_rate: int = 44100
    channels: int = 2
    track_type: str = "voice"


@dataclass
class Track:
    """轨道"""
    track_id: str
    track_type: str
    assets: List[Asset] = field(default_factory=list)
    enabled: bool = True
    mute: bool = False
    volume: float = 1.0
    effects: List[str] = field(default_factory=list)


@dataclass
class Timeline:
    """时间线"""
    timeline_id: str
    duration: float
    tracks: Dict[str, Track] = field(default_factory=dict)
    markers: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Project:
    """项目"""
    project_id: str
    project_name: str
    settings: ProductionSettings
    timeline: Timeline
    style_guide: ProjectStyleGuide
    assets: Dict[str, Asset] = field(default_factory=dict)
    scripts: Optional[ScriptParseResult] = None


@dataclass
class GenerationTask:
    """生成任务"""
    task_id: str
    task_type: ModelFunctionType
    params: Dict[str, Any]
    dependencies: List[str] = field(default_factory=list)
    priority: int = 0


@dataclass
class FusionResult:
    """融合结果"""
    success: bool
    output_path: Optional[str] = None
    project: Optional[Project] = None
    tasks_executed: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    duration: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseComponent(ABC):
    """基础组件"""
    
    @abstractmethod
    def process(self, *args, **kwargs):
        """处理"""
        pass


class VideoComponent(BaseComponent):
    """视频组件"""
    
    def __init__(self):
        self.image_to_video = ImageToVideoGenerator()
        self.style_transfer = StyleTransferEngine()
        self.format_converter = FormatConverter()
    
    def process(self, task: GenerationTask, project: Project) -> List[VideoAsset]:
        """处理视频任务"""
        assets = []
        
        if task.task_type == ModelFunctionType.IMAGE_TO_VIDEO:
            config = task.params.get("config")
            img_path = task.params.get("image_path")
            result = self.image_to_video.generate(img_path, config)
            if result.success:
                asset = VideoAsset(
                    asset_id=f"vid_{task.task_id}",
                    asset_type="video",
                    path=result.video_path or "",
                    duration=result.duration or 0,
                    fps=result.fps or 24,
                    resolution=result.resolution or (1920, 1080)
                )
                assets.append(asset)
        
        return assets


class AudioComponent(BaseComponent):
    """音频组件"""
    
    def __init__(self):
        self.enhanced_audio = EnhancedAudioEngine()
        self.format_converter = FormatConverter()
    
    def process(self, task: GenerationTask, project: Project) -> List[AudioAsset]:
        """处理音频任务"""
        assets = []
        
        if task.task_type == ModelFunctionType.SCRIPT_TO_AUDIO:
            script = task.params.get("script")
            parse_result, plans = self.enhanced_audio.process_script(
                script,
                project.style_guide
            )
            
            for scene in parse_result.scenes:
                asset = AudioAsset(
                    asset_id=f"aud_scene_{scene.scene_id}",
                    asset_type="audio",
                    path=f"output/audio/scene_{scene.scene_id}.wav",
                    track_type="voice"
                )
                assets.append(asset)
        
        return assets


class FusionComponent(BaseComponent):
    """融合组件"""
    
    def __init__(self):
        self.validator = get_consistency_validator()
    
    def process(self, project: Project) -> FusionResult:
        """处理融合任务"""
        validation_data = {
            "sample_rate": 44100,
            "fps": project.settings.fps
        }
        
        self.validator.validate(
            ModelFunctionType.AV_FUSION,
            validation_data,
            TouchPoint.PRE_PROCESSING
        )
        
        try:
            logger.info(f"Executing fusion for project {project.project_id}")
            
            return FusionResult(
                success=True,
                project=project,
                tasks_executed=len(project.timeline.tracks),
                duration=project.timeline.duration
            )
        except Exception as e:
            logger.error(f"Fusion failed: {e}")
            return FusionResult(
                success=False,
                errors=[str(e)]
            )


class WorkflowEngine:
    """工作流引擎"""
    
    def __init__(self):
        self.tasks: Dict[str, GenerationTask] = {}
        self.task_order: List[str] = []
        self.audio_component = AudioComponent()
        self.video_component = VideoComponent()
        self.fusion_component = FusionComponent()
        self.task_results: Dict[str, Any] = {}
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def add_task(self, task: GenerationTask):
        """添加任务"""
        self.tasks[task.task_id] = task
        self.task_order.append(task.task_id)
    
    def build_workflow(self, project: Project):
        """构建工作流"""
        self.tasks.clear()
        self.task_order.clear()
        self.task_results.clear()
        self.errors.clear()
        self.warnings.clear()
        
        if project.scripts:
            script_task = GenerationTask(
                task_id="script_to_audio",
                task_type=ModelFunctionType.SCRIPT_TO_AUDIO,
                params={"script": project.scripts},
                priority=1
            )
            self.add_task(script_task)
        
        if "visual" in project.timeline.tracks:
            visual_task = GenerationTask(
                task_id="video_gen",
                task_type=ModelFunctionType.SCENE_GENERATION,
                params={"project": project},
                priority=2
            )
            self.add_task(visual_task)
        
        fusion_task = GenerationTask(
            task_id="fusion",
            task_type=ModelFunctionType.AV_FUSION,
            params={"project": project},
            dependencies=[t for t in self.task_order if t != "fusion"],
            priority=10
        )
        self.add_task(fusion_task)
    
    def _resolve_task_order(self) -> List[str]:
        """解析任务依赖，返回拓扑排序后的执行顺序"""
        visited = set()
        temp = set()
        order = []
        cycle_detected = False

        def visit(task_id: str):
            nonlocal cycle_detected
            if cycle_detected:
                return
            if task_id in temp:
                cycle_detected = True
                self.errors.append(f"检测到任务依赖循环: {task_id}")
                return
            if task_id in visited:
                return
            
            temp.add(task_id)
            task = self.tasks.get(task_id)
            if task:
                for dep_id in task.dependencies:
                    if dep_id in self.tasks:
                        visit(dep_id)
            
            temp.remove(task_id)
            visited.add(task_id)
            order.append(task_id)

        for task_id in self.tasks:
            if task_id not in visited:
                visit(task_id)
        
        if cycle_detected:
            return []
        
        return order
    
    def _execute_task(self, task: GenerationTask, project: Project) -> Any:
        """执行单个任务"""
        try:
            logger.info(f"执行任务: {task.task_id} ({task.task_type})")
            
            if task.task_type == ModelFunctionType.SCRIPT_TO_AUDIO:
                assets = self.audio_component.process(task, project)
                return assets
            
            elif task.task_type == ModelFunctionType.SCENE_GENERATION:
                assets = self.video_component.process(task, project)
                return assets
            
            elif task.task_type == ModelFunctionType.AV_FUSION:
                return self.fusion_component.process(project)
            
            else:
                self.warnings.append(f"未知任务类型: {task.task_type}")
                return None
        
        except Exception as e:
            logger.error(f"任务执行失败 {task.task_id}: {e}")
            self.errors.append(f"任务 {task.task_id} 失败: {str(e)}")
            raise
    
    def execute(self, project: Project) -> FusionResult:
        """执行工作流 - 支持依赖解析和顺序执行"""
        start_time = time.time()
        
        try:
            logger.info(f"开始执行工作流，项目: {project.project_id}")
            
            # 解析任务执行顺序
            execution_order = self._resolve_task_order()
            
            if not execution_order and self.errors:
                return FusionResult(
                    success=False,
                    project=project,
                    tasks_executed=0,
                    errors=self.errors,
                    warnings=self.warnings
                )
            
            logger.info(f"任务执行顺序: {execution_order}")
            
            # 按顺序执行任务
            tasks_executed = 0
            for task_id in execution_order:
                task = self.tasks.get(task_id)
                if not task:
                    continue
                
                # 检查依赖是否已完成
                for dep_id in task.dependencies:
                    if dep_id not in self.task_results and dep_id in self.tasks:
                        self.errors.append(f"任务 {task_id} 依赖的任务 {dep_id} 未完成")
                        return FusionResult(
                            success=False,
                            project=project,
                            tasks_executed=tasks_executed,
                            errors=self.errors,
                            warnings=self.warnings
                        )
                
                # 执行任务
                try:
                    result = self._execute_task(task, project)
                    self.task_results[task_id] = result
                    tasks_executed += 1
                except Exception:
                    # 继续累加错误信息，不再继续执行后续任务
                    break
            
            duration = time.time() - start_time
            
            if self.errors:
                logger.warning(f"工作流执行完成，但有 {len(self.errors)} 个错误")
                return FusionResult(
                    success=False,
                    project=project,
                    tasks_executed=tasks_executed,
                    errors=self.errors,
                    warnings=self.warnings,
                    duration=duration,
                    metadata={"task_results": self.task_results}
                )
            
            logger.info(f"工作流执行成功，共执行 {tasks_executed} 个任务，耗时 {duration:.2f}秒")
            
            return FusionResult(
                success=True,
                project=project,
                tasks_executed=tasks_executed,
                warnings=self.warnings,
                duration=duration,
                metadata={"task_results": self.task_results}
            )
        
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"工作流执行异常: {e}")
            
            if str(e) not in self.errors:
                self.errors.append(f"工作流异常: {str(e)}")
            
            return FusionResult(
                success=False,
                project=project,
                tasks_executed=0,
                errors=self.errors,
                warnings=self.warnings,
                duration=duration
            )


class AVMultimodalFusionEngine:
    """音视频多模态融合引擎 - 电影级融合能力"""
    
    def __init__(self):
        self.video_component = VideoComponent()
        self.audio_component = AudioComponent()
        self.fusion_component = FusionComponent()
        self.workflow_engine = WorkflowEngine()
    
    def create_project(
        self,
        project_name: str,
        style_guide: ProjectStyleGuide,
        settings: Optional[ProductionSettings] = None
    ) -> Project:
        """创建项目"""
        settings = settings or ProductionSettings()
        
        timeline = Timeline(
            timeline_id=f"tl_{project_name}",
            duration=0.0,
            tracks={
                "video": Track(track_id="video", track_type="video"),
                "voice": Track(track_id="voice", track_type="audio"),
                "music": Track(track_id="music", track_type="audio"),
                "sfxs": Track(track_id="sfxs", track_type="audio")
            }
        )
        
        return Project(
            project_id=f"proj_{project_name}",
            project_name=project_name,
            settings=settings,
            timeline=timeline,
            style_guide=style_guide
        )
    
    def add_asset(self, project: Project, asset: Asset) -> Project:
        """添加资产"""
        project.assets[asset.asset_id] = asset
        
        track_type = asset.asset_type if asset.asset_type in project.timeline.tracks else "video"
        if track_type in project.timeline.tracks:
            project.timeline.tracks[track_type].assets.append(asset)
        
        return project
    
    def generate_independent_audio(
        self,
        project: Project,
        prompt: str,
        genre: MusicalGenre
    ) -> AudioAsset:
        """独立生成音频"""
        engine = AudioPromptEngine()
        engine.optimize_prompt(prompt, genre)
        
        asset = AudioAsset(
            asset_id=f"aud_gen_{len(project.assets)}",
            asset_type="audio",
            path="output/audio/generated.wav",
            track_type="music"
        )
        
        return self.add_asset(project, asset)
    
    def generate_independent_video(
        self,
        project: Project,
        image_path: str,
        config: Any
    ) -> VideoAsset:
        """独立生成视频"""
        result = self.video_component.image_to_video.generate(image_path, config)
        
        if result.success:
            asset = VideoAsset(
                asset_id=f"vid_gen_{len(project.assets)}",
                asset_type="video",
                path=result.video_path or "",
                duration=result.duration or 0,
                fps=result.fps or 24
            )
            return self.add_asset(project, asset)
        
        return None
    
    def fuse_cinematic(
        self,
        project: Project,
        script: Optional[str] = None
    ) -> FusionResult:
        """电影级融合"""
        if script:
            parse_result, plans = self.audio_component.enhanced_audio.process_script(
                script,
                project.style_guide
            )
            project.scripts = parse_result
        
        self.workflow_engine.build_workflow(project)
        result = self.workflow_engine.execute(project)
        
        self.fusion_component.process(project)
        result.output_path = project.settings.output_path
        
        return result
    
    def get_project_stats(self, project: Project) -> Dict[str, Any]:
        """获取项目统计"""
        stats = {
            "project_id": project.project_id,
            "total_assets": len(project.assets),
            "tracks": len(project.timeline.tracks),
            "duration": project.timeline.duration,
            "quality": project.settings.quality.value
        }
        
        return stats
