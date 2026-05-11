"""工作流整合模块 - 同类型项目的整合性组合统一"""
import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum
import copy

from src.model_dispatcher.type_system import get_consistency_validator
from src.multimodal.audio_prompt_engine import MusicalGenre
from src.multimodal.enhanced_audio_engine import (
    ProjectStyleGuide,
    EnhancedAudioEngine,
)
from src.multimodal.av_multimodal_fusion import (
    AVMultimodalFusionEngine,
    Project,
    ProductionSettings,
    ProductionQuality,
    FusionResult,
)

logger = logging.getLogger("hydraflow.multimodal.workflow_integration")


class ProjectType(str, Enum):
    """项目类型"""
    SHORT_FILM = "short_film"
    FEATURE_FILM = "feature_film"
    DOCUMENTARY = "documentary"
    MUSIC_VIDEO = "music_video"
    PODCAST = "podcast"
    ADVERTISEMENT = "advertisement"
    AUDIOBOOK = "audiobook"
    ANIMATION = "animation"


class IntegrationStrategy(str, Enum):
    """整合策略"""
    SEQUENTIAL = "sequential"  # 顺序处理
    PARALLEL = "parallel"      # 并行处理
    PIPELINE = "pipeline"      # 流水线
    MODULAR = "modular"        # 模块化


@dataclass
class ProjectTemplate:
    """项目模板"""
    template_id: str
    template_name: str
    project_type: ProjectType
    default_settings: ProductionSettings
    default_style_guide: ProjectStyleGuide
    recommended_workflow: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BatchConfig:
    """批量处理配置"""
    batch_id: str
    strategy: IntegrationStrategy
    concurrency_limit: int = 4
    retry_attempts: int = 3
    quality_check: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BatchResult:
    """批量处理结果"""
    batch_id: str
    total_projects: int
    successful: int
    failed: int
    results: List[FusionResult] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    total_duration: float = 0.0


class ProjectLibrary:
    """项目库 - 项目模板管理"""
    
    def __init__(self):
        self.templates: Dict[str, ProjectTemplate] = {}
        self._init_default_templates()
    
    def _init_default_templates(self):
        """初始化默认模板"""
        
        # 短片模板
        short_film_style = ProjectStyleGuide(
            project_id="short_film_template",
            genre=MusicalGenre.CINEMATIC,
            overall_mood="dramatic",
            target_era="contemporary",
            base_tempo_range=(70.0, 130.0),
            base_dynamics=0.6,
            reverb_character="large_hall",
            orchestration_style="hybrid",
            mixing_balance={"voice": 0.6, "music": 0.3, "sfxs": 0.1}
        )
        
        short_film_settings = ProductionSettings(
            quality=ProductionQuality.CINEMATIC,
            resolution=(1920, 1080),
            fps=24.0,
            bitrate_video="15M"
        )
        
        short_film_template = ProjectTemplate(
            template_id="short_film",
            template_name="Short Film Template",
            project_type=ProjectType.SHORT_FILM,
            default_settings=short_film_settings,
            default_style_guide=short_film_style,
            recommended_workflow=[
                "script_parsing",
                "character_voiceover",
                "scene_generation",
                "background_music",
                "foley",
                "av_fusion"
            ]
        )
        
        # 播客模板
        podcast_style = ProjectStyleGuide(
            project_id="podcast_template",
            genre=MusicalGenre.LO_FI,
            overall_mood="relaxed",
            target_era="contemporary",
            base_tempo_range=(60.0, 90.0),
            base_dynamics=0.3,
            reverb_character="small_room",
            orchestration_style="minimal",
            mixing_balance={"voice": 0.8, "music": 0.15, "sfxs": 0.05}
        )
        
        podcast_settings = ProductionSettings(
            quality=ProductionQuality.BROADCAST,
            resolution=(1280, 720),
            fps=30.0,
            bitrate_video="5M"
        )
        
        podcast_template = ProjectTemplate(
            template_id="podcast",
            template_name="Podcast Template",
            project_type=ProjectType.PODCAST,
            default_settings=podcast_settings,
            default_style_guide=podcast_style,
            recommended_workflow=[
                "script_parsing",
                "voiceover",
                "background_music",
                "audio_export"
            ]
        )
        
        # 音乐视频模板
        music_video_style = ProjectStyleGuide(
            project_id="music_video_template",
            genre=MusicalGenre.ELECTRONIC,
            overall_mood="energetic",
            target_era="contemporary",
            base_tempo_range=(100.0, 160.0),
            base_dynamics=0.8,
            reverb_character="medium_hall",
            orchestration_style="electronic",
            mixing_balance={"voice": 0.2, "music": 0.7, "sfxs": 0.1}
        )
        
        music_video_settings = ProductionSettings(
            quality=ProductionQuality.CINEMATIC,
            resolution=(3840, 2160),
            fps=24.0,
            bitrate_video="40M"
        )
        
        music_video_template = ProjectTemplate(
            template_id="music_video",
            template_name="Music Video Template",
            project_type=ProjectType.MUSIC_VIDEO,
            default_settings=music_video_settings,
            default_style_guide=music_video_style,
            recommended_workflow=[
                "music_synchronization",
                "visual_style_transfer",
                "video_effects",
                "av_fusion"
            ]
        )
        
        self.templates["short_film"] = short_film_template
        self.templates["podcast"] = podcast_template
        self.templates["music_video"] = music_video_template
    
    def get_template(self, template_id: str) -> Optional[ProjectTemplate]:
        """获取模板"""
        return self.templates.get(template_id)
    
    def list_templates(self) -> List[ProjectTemplate]:
        """列出所有模板"""
        return list(self.templates.values())
    
    def register_template(self, template: ProjectTemplate):
        """注册模板"""
        self.templates[template.template_id] = template
        logger.info(f"Registered template: {template.template_name}")


class WorkflowIntegrator:
    """工作流整合器"""
    
    def __init__(self):
        self.library = ProjectLibrary()
        self.fusion_engine = AVMultimodalFusionEngine()
        self.audio_engine = EnhancedAudioEngine()
        self.projects: Dict[str, Project] = {}
    
    def create_project_from_template(
        self,
        template_id: str,
        project_name: str
    ) -> Project:
        """从模板创建项目"""
        template = self.library.get_template(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")
        
        settings = copy.deepcopy(template.default_settings)
        style_guide = copy.deepcopy(template.default_style_guide)
        style_guide.project_id = project_name
        
        project = self.fusion_engine.create_project(
            project_name=project_name,
            style_guide=style_guide,
            settings=settings
        )
        
        self.projects[project.project_id] = project
        return project
    
    def batch_create_projects(
        self,
        template_id: str,
        project_names: List[str]
    ) -> List[Project]:
        """批量创建项目"""
        projects = []
        for name in project_names:
            try:
                project = self.create_project_from_template(template_id, name)
                projects.append(project)
            except Exception as e:
                logger.error(f"Failed to create project {name}: {e}")
        return projects
    
    def apply_workflow_to_project(
        self,
        project: Project,
        workflow_steps: Optional[List[str]] = None
    ) -> FusionResult:
        """应用工作流到项目"""
        if not workflow_steps:
            for template in self.library.list_templates():
                if template.project_type == ProjectType.SHORT_FILM:
                    workflow_steps = template.recommended_workflow
                    break
        
        logger.info(f"Applying workflow to {project.project_name}: {workflow_steps}")
        
        result = FusionResult(
            success=True,
            project=project,
            tasks_executed=len(workflow_steps or [])
        )
        
        fusion_result = self.fusion_engine.fuse_cinematic(project)
        result.output_path = fusion_result.output_path
        
        return result
    
    def batch_process_projects(
        self,
        projects: List[Project],
        config: BatchConfig
    ) -> BatchResult:
        """批量处理项目"""
        batch_result = BatchResult(
            batch_id=config.batch_id,
            total_projects=len(projects),
            successful=0,
            failed=0
        )
        
        for project in projects:
            try:
                result = self.apply_workflow_to_project(project)
                if result.success:
                    batch_result.successful += 1
                    batch_result.results.append(result)
                else:
                    batch_result.failed += 1
                    batch_result.errors.extend(result.errors)
            except Exception as e:
                batch_result.failed += 1
                batch_result.errors.append(f"Project {project.project_name}: {e}")
        
        return batch_result
    
    def merge_projects(
        self,
        main_project: Project,
        secondary_projects: List[Project],
        preserve_style: bool = True
    ) -> Project:
        """合并多个项目"""
        merged = copy.deepcopy(main_project)
        
        for secondary in secondary_projects:
            for asset_id, asset in secondary.assets.items():
                if asset_id not in merged.assets:
                    merged.assets[asset_id] = copy.deepcopy(asset)
                    track_type = asset.asset_type if asset.asset_type in merged.timeline.tracks else "video"
                    if track_type in merged.timeline.tracks:
                        merged.timeline.tracks[track_type].assets.append(asset)
        
        if preserve_style:
            merged.style_guide = main_project.style_guide
        
        return merged
    
    def export_project_package(
        self,
        project: Project,
        output_path: str
    ) -> Dict[str, Any]:
        """导出项目包"""
        package = {
            "project_id": project.project_id,
            "project_name": project.project_name,
            "settings": {
                "quality": project.settings.quality.value,
                "resolution": project.settings.resolution,
                "fps": project.settings.fps
            },
            "style_guide": {
                "genre": project.style_guide.genre.value,
                "mood": project.style_guide.overall_mood
            },
            "assets_count": len(project.assets),
            "export_path": output_path
        }
        
        logger.info(f"Exported project package: {project.project_name}")
        return package


class UnifiedProjectManager:
    """统一项目管理器 - 整合所有功能"""
    
    def __init__(self):
        self.integrator = WorkflowIntegrator()
        self.validator = get_consistency_validator()
    
    def quick_start(
        self,
        project_type: ProjectType,
        project_name: str,
        script_text: Optional[str] = None
    ) -> Project:
        """快速启动项目"""
        template_map = {
            ProjectType.SHORT_FILM: "short_film",
            ProjectType.PODCAST: "podcast",
            ProjectType.MUSIC_VIDEO: "music_video"
        }
        
        template_id = template_map.get(project_type, "short_film")
        project = self.integrator.create_project_from_template(template_id, project_name)
        
        if script_text:
            parse_result, plans = self.integrator.audio_engine.process_script(
                script_text,
                project.style_guide
            )
            project.scripts = parse_result
        
        return project
    
    def complete_production(
        self,
        project: Project
    ) -> FusionResult:
        """完整制作流程"""
        return self.integrator.apply_workflow_to_project(project)
    
    def get_project_status(self, project_id: str) -> Optional[Dict[str, Any]]:
        """获取项目状态"""
        project = self.integrator.projects.get(project_id)
        if project:
            return {
                "project_id": project_id,
                "project_name": project.project_name,
                "assets_count": len(project.assets),
                "timeline_duration": project.timeline.duration
            }
        return None
