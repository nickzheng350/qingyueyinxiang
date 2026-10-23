"""影视制作管线：把镜头表编排为可交付的成片清单、时间线与剪辑决策表。

该层是**预生产与制作编排**中枢：

* 对每个镜头执行生产参数一致性校验（复用 type_system 的一致性校验器）；
* 把规划资产登记进既有 AVMultimodalFusionEngine 的项目 / 时间线；
* 复用 EnhancedAudioEngine 生成对白 / 配音计划，复用 ImageToVideoGenerator
  驱动图生视频，并以一致性校验器约束风格与运动参数；
* 产出 ProductionManifest（JSON 可序列化）与 CMX3600 风格 EDL，
  供后期（NLE）直接消费。

实际像素 / 音频合成交由已注册的模型后端；本地后端为占位实现时，
管线产出的是"渲染就绪"的制作规划与交付物。
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from src.filmmaking.director import Director, Storyboard
from src.filmmaking.script import CameraMovement, Screenplay
from src.model_dispatcher.type_system import (
    ModelFunctionType,
    TouchPoint,
    get_consistency_validator,
)
from src.multimodal.av_multimodal_fusion import (
    AudioAsset,
    AVMultimodalFusionEngine,
    ProductionSettings,
    Project,
    VideoAsset,
)
from src.multimodal.enhanced_audio_engine import (
    EnhancedAudioEngine,
    MusicalGenre,
    ProjectStyleGuide,
)
from src.multimodal.image_to_video import (
    ImageToVideoConfig,
    ImageToVideoGenerator,
    VideoMotionType,
)
from src.multimodal.style_transfer import ArtStyle

logger = logging.getLogger("hydraflow.filmmaking.pipeline")

# 运镜 -> 图生视频运动类型 的映射。
_CAMERA_TO_MOTION: Dict[str, VideoMotionType] = {
    "static": VideoMotionType.CUSTOM,
    "pan": VideoMotionType.CAMERA_PAN,
    "tilt": VideoMotionType.CAMERA_TILT,
    "zoom": VideoMotionType.CAMERA_ZOOM,
    "dolly": VideoMotionType.SUBJECT_MOTION,
    "truck": VideoMotionType.SUBJECT_MOTION,
    "crane": VideoMotionType.CAMERA_PAN,
    "steadicam": VideoMotionType.SUBJECT_MOTION,
    "handheld": VideoMotionType.SUBJECT_MOTION,
    "aerial": VideoMotionType.CAMERA_PAN,
    "follow": VideoMotionType.SUBJECT_MOTION,
}

# 风格预设 -> 艺术风格 的映射（未知预设回落到 CUSTOM）。
_STYLE_TO_ART: Dict[str, ArtStyle] = {
    "cinematic": ArtStyle.CUSTOM,
    "anime": ArtStyle.ANIME,
    "cyberpunk": ArtStyle.CYBERPUNK,
    "watercolor": ArtStyle.WATERCOLOR,
    "oil_painting": ArtStyle.OIL_PAINTING,
    "neon": ArtStyle.NEON,
}


@dataclass
class ProductionManifest:
    """成片清单：整部影片的可序列化制作蓝图。"""

    title: str
    logline: str
    genre: str
    total_duration_sec: float
    shot_count: int
    scenes: List[Dict[str, Any]] = field(default_factory=list)
    audio_tracks: List[Dict[str, Any]] = field(default_factory=list)
    style_guide: Dict[str, Any] = field(default_factory=dict)
    continuity_sheet: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "logline": self.logline,
            "genre": self.genre,
            "total_duration_sec": round(self.total_duration_sec, 3),
            "shot_count": self.shot_count,
            "scenes": self.scenes,
            "audio_tracks": self.audio_tracks,
            "style_guide": self.style_guide,
            "continuity_sheet": self.continuity_sheet,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)


@dataclass
class ProductionResult:
    """制作结果：管线一次 produce 的完整输出。"""

    success: bool
    screenplay_title: str
    shots_total: int
    shots_completed: int
    manifest: ProductionManifest
    timeline: Any
    edl: str
    project: Project
    edl_xml: str = ""
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    duration_sec: float = 0.0
    stats: Dict[str, Any] = field(default_factory=dict)


class FilmProductionPipeline:
    """影视制作管线：导演产出 -> 资产生成规划 -> 时间线 / EDL / 清单。"""

    def __init__(
        self,
        style_guide: Optional[ProjectStyleGuide] = None,
        settings: Optional[ProductionSettings] = None,
    ):
        self.director = Director()
        self.av_engine = AVMultimodalFusionEngine()
        self.img2vid = ImageToVideoGenerator()
        self.audio_engine = EnhancedAudioEngine()
        self.validator = get_consistency_validator()
        self.style_guide = style_guide
        self.settings = settings or ProductionSettings()

    def produce(self, screenplay: Screenplay, script_text: str = "") -> ProductionResult:
        storyboard = self.director.plan(screenplay)
        style_guide = self.style_guide or self._default_style_guide(screenplay.title)
        project = self.av_engine.create_project(screenplay.title, style_guide, self.settings)

        shot_start, scene_start, total = self._schedule(storyboard)
        project.timeline.duration = total

        video_assets = self._produce_shots(storyboard, project, shot_start)
        audio_assets = self._produce_audio(script_text, style_guide, project, storyboard, scene_start, total)
        self._assemble_timeline(project, storyboard, video_assets, audio_assets)
        edl = self._build_edl(storyboard, shot_start)
        edl_xml = self._build_xml(storyboard, shot_start, scene_start, total)
        manifest = self._build_manifest(
            screenplay, storyboard, video_assets, audio_assets, style_guide
        )
        stats = self.av_engine.get_project_stats(project)
        warnings = self._collect_warnings(storyboard)

        return ProductionResult(
            success=True,
            screenplay_title=screenplay.title,
            shots_total=storyboard.screenplay.total_shots,
            shots_completed=len(video_assets),
            manifest=manifest,
            timeline=project.timeline,
            edl=edl,
            edl_xml=edl_xml,
            project=project,
            errors=[],
            warnings=warnings,
            duration_sec=total,
            stats=stats,
        )

    # -- 时间线调度 ------------------------------------------------------

    def _schedule(self, storyboard: Storyboard) -> "tuple[Dict[str, float], Dict[str, float], float]":
        shot_start: Dict[str, float] = {}
        scene_start: Dict[str, float] = {}
        cursor = 0.0
        for shot in storyboard.shots:
            shot_start[shot.shot_id] = cursor
            if shot.scene_id not in scene_start:
                scene_start[shot.scene_id] = cursor
            cursor += shot.duration_sec
        return shot_start, scene_start, cursor

    # -- 镜头资产规划 ----------------------------------------------------

    def _produce_shots(
        self, storyboard: Storyboard, project: Project, shot_start: Dict[str, float]
    ) -> List[VideoAsset]:
        assets: List[VideoAsset] = []
        fps = int(self.settings.fps)
        width, height = self.settings.resolution

        for shot in storyboard.shots:
            config = ImageToVideoConfig(
                duration=shot.duration_sec,
                fps=fps,
                width=width,
                height=height,
                motion_type=self._motion_for(shot.camera_movement),
                motion_strength=0.5,
            )
            # 实际驱动图生视频组件（内部完成一致性校验，失败以 .success 返回）。
            gen_result = self.img2vid.generate(
                image_path=shot.keyframe_path or f"plan://{shot.shot_id}.png",
                config=config,
                model_id=None,
            )
            if not gen_result.success:
                logger.warning("镜头 %s 图生视频失败: %s", shot.shot_id, gen_result.error_message)
                continue

            # 风格迁移一致性校验：约束画面尺寸边界，供后端合成时使用。
            self.validator.validate(
                ModelFunctionType.IMAGE_STYLE_TRANSFER,
                {"width": width, "height": height},
                TouchPoint.PRE_PROCESSING,
            )

            asset = VideoAsset(
                asset_id=shot.shot_id,
                asset_type="video",
                path=shot.video_path or gen_result.video_path or f"plan://{shot.shot_id}.mp4",
                duration=shot.duration_sec,
                fps=fps,
                resolution=self.settings.resolution,
                start_time=shot_start[shot.shot_id],
                metadata={
                    "image_prompt": shot.image_prompt,
                    "motion_prompt": shot.motion_prompt,
                    "continuity_anchor": shot.continuity_anchor,
                    "shot_size": shot.shot_size.value,
                    "transition": shot.transition,
                    "style_preset": self._art_style(shot.style_preset).value,
                },
            )
            self.av_engine.add_asset(project, asset)
            assets.append(asset)
        return assets

    def _produce_audio(
        self,
        script_text: str,
        style_guide: ProjectStyleGuide,
        project: Project,
        storyboard: Storyboard,
        scene_start: Dict[str, float],
        total: float,
    ) -> List[AudioAsset]:
        assets: List[AudioAsset] = []
        if script_text:
            parse_result, _plans = self.audio_engine.process_script(script_text, style_guide)
            for scene in parse_result.scenes:
                scene_id = scene.scene_id
                duration = max(1.0, sum(line.end_time for line in scene.dialogue_lines))
                asset = AudioAsset(
                    asset_id=f"aud_{scene_id}",
                    asset_type="voice",
                    path=f"plan://{scene_id}_voice.wav",
                    track_type="voice",
                    duration=duration,
                    start_time=scene_start.get(scene_id, 0.0),
                    metadata={"scene_id": scene_id, "lines": len(scene.dialogue_lines)},
                )
                self.av_engine.add_asset(project, asset)
                assets.append(asset)

        music = AudioAsset(
            asset_id=f"mus_{project.project_id}",
            asset_type="music",
            path=f"plan://{project.project_id}_score.wav",
            track_type="music",
            duration=total,
            start_time=0.0,
            metadata={"genre": style_guide.genre.value},
        )
        self.av_engine.add_asset(project, music)
        assets.append(music)

        # 每个场景的环境音效轨（sfxs），便于后期精修。
        for fscene in storyboard.screenplay.scenes:
            scene_id = fscene.scene_id
            duration = sum(s.duration_sec for s in fscene.shots)
            sfx = AudioAsset(
                asset_id=f"sfx_{scene_id}",
                asset_type="sfxs",
                path=f"plan://{scene_id}_amb.wav",
                track_type="sfxs",
                duration=duration,
                start_time=scene_start.get(scene_id, 0.0),
                metadata={"scene_id": scene_id, "kind": "ambience"},
            )
            self.av_engine.add_asset(project, sfx)
            assets.append(sfx)
        return assets

    def _assemble_timeline(
        self,
        project: Project,
        storyboard: Storyboard,
        video_assets: List[VideoAsset],
        audio_assets: List[AudioAsset],
    ) -> None:
        project.timeline.metadata = {
            "title": project.project_name,
            "shot_count": len(video_assets),
            "audio_track_count": len(audio_assets),
        }

    # -- 交付物 ----------------------------------------------------------

    def _build_edl(self, storyboard: Storyboard, shot_start: Dict[str, float]) -> str:
        fps = int(self.settings.fps)
        lines = [
            f"TITLE: {storyboard.screenplay.title}",
            "FCM: NON-DROP FRAME",
            "",
        ]
        for index, shot in enumerate(storyboard.shots, start=1):
            record_in = shot_start[shot.shot_id]
            record_out = record_in + shot.duration_sec
            event = (
                f"{index:03d}  {shot.shot_id.upper()}    V     C        "
                f"{_sec_to_tc(0.0, fps)} {_sec_to_tc(shot.duration_sec, fps)} "
                f"{_sec_to_tc(record_in, fps)} {_sec_to_tc(record_out, fps)}"
            )
            lines.append(event)

        # 音频事件（对白 / 音乐 / 音效）作为 A 轨事件写入 EDL。
        lines.append("")
        lines.append("* AUDIO EVENTS")
        audio_index = 1
        for asset in self._audio_event_list(storyboard, shot_start):
            start = asset["start"]
            end = start + asset["duration"]
            event = (
                f"{audio_index:03d}  {asset['id'].upper()}    A     C        "
                f"{_sec_to_tc(0.0, fps)} {_sec_to_tc(asset['duration'], fps)} "
                f"{_sec_to_tc(start, fps)} {_sec_to_tc(end, fps)}"
            )
            lines.append(event)
            audio_index += 1
        return "\n".join(lines)

    def _audio_event_list(
        self, storyboard: Storyboard, shot_start: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        events: List[Dict[str, Any]] = []
        for scene in storyboard.screenplay.scenes:
            if not scene.shots:
                continue
            start = shot_start.get(scene.shots[0].shot_id, 0.0)
            duration = sum(s.duration_sec for s in scene.shots)
            if scene.lines:
                events.append({"id": f"aud_{scene.scene_id}", "start": start, "duration": duration})
            events.append({"id": f"sfx_{scene.scene_id}", "start": start, "duration": duration})
        total = storyboard.screenplay.total_duration_sec
        events.append({"id": f"mus_{storyboard.screenplay.title}", "start": 0.0, "duration": total})
        return events

    def _build_xml(
        self, storyboard: Storyboard, shot_start: Dict[str, float],
        scene_start: Dict[str, float], total: float,
    ) -> str:
        """生成 NLE 可交换 XML（视频轨 + 音频轨：对白 / 音乐 / 音效）。"""
        import xml.etree.ElementTree as ET

        root = ET.Element(
            "hydraflow_interchange",
            {"version": "1.0", "title": storyboard.screenplay.title, "fps": str(int(self.settings.fps))},
        )
        sequence = ET.SubElement(root, "sequence", {"duration": f"{total:.3f}"})

        video_track = ET.SubElement(sequence, "track", {"type": "video"})
        for index, shot in enumerate(storyboard.shots, start=1):
            start = shot_start[shot.shot_id]
            clip = ET.SubElement(
                video_track, "clip",
                {
                    "index": str(index),
                    "id": shot.shot_id,
                    "name": shot.description,
                    "start": f"{start:.3f}",
                    "duration": f"{shot.duration_sec:.3f}",
                    "in": "0.000",
                    "out": f"{shot.duration_sec:.3f}",
                    "shot_size": shot.shot_size.value,
                    "camera_movement": shot.camera_movement.value,
                    "transition": shot.transition,
                },
            )
            clip.text = shot.image_prompt

        for role, asset_type in (("voice", "voice"), ("music", "music"), ("sfxs", "sfxs")):
            track = ET.SubElement(sequence, "track", {"type": "audio", "role": role})
            for scene in storyboard.screenplay.scenes:
                if not scene.shots:
                    continue
                start = shot_start[scene.shots[0].shot_id]
                duration = sum(s.duration_sec for s in scene.shots)
                if role == "voice" and not scene.lines:
                    continue
                clip = ET.SubElement(
                    track, "clip",
                    {
                        "id": f"{asset_type}_{scene.scene_id}",
                        "name": f"{role}:{scene.scene_id}",
                        "start": f"{start:.3f}",
                        "duration": f"{duration:.3f}",
                    },
                )
                clip.text = scene.location
            if role == "music":
                clip = ET.SubElement(
                    track, "clip",
                    {
                        "id": f"music_{storyboard.screenplay.title}",
                        "name": "score",
                        "start": "0.000",
                        "duration": f"{total:.3f}",
                    },
                )
                clip.text = "original score"
        return ET.tostring(root, encoding="unicode")

    def _build_manifest(
        self,
        screenplay: Screenplay,
        storyboard: Storyboard,
        video_assets: List[VideoAsset],
        audio_assets: List[AudioAsset],
        style_guide: ProjectStyleGuide,
    ) -> ProductionManifest:
        scenes: List[Dict[str, Any]] = []
        for scene in screenplay.scenes:
            scenes.append(
                {
                    "scene_id": scene.scene_id,
                    "scene_number": scene.scene_number,
                    "location": scene.location,
                    "time_of_day": scene.time_of_day,
                    "interior": scene.interior,
                    "mood": scene.mood,
                    "characters": scene.characters,
                    "shots": [
                        {
                            "shot_id": shot.shot_id,
                            "shot_size": shot.shot_size.value,
                            "camera_movement": shot.camera_movement.value,
                            "lighting": shot.lighting.value,
                            "duration_sec": shot.duration_sec,
                            "transition": shot.transition,
                            "continuity_anchor": shot.continuity_anchor,
                        }
                        for shot in scene.shots
                    ],
                }
            )
        audio_tracks = [
            {
                "asset_id": asset.asset_id,
                "track_type": asset.track_type,
                "duration": asset.duration,
                "start": asset.start_time,
            }
            for asset in audio_assets
        ]
        return ProductionManifest(
            title=screenplay.title,
            logline=screenplay.logline,
            genre=screenplay.genre,
            total_duration_sec=storyboard.screenplay.total_duration_sec,
            shot_count=len(video_assets),
            scenes=scenes,
            audio_tracks=audio_tracks,
            style_guide={
                "genre": style_guide.genre.value,
                "overall_mood": style_guide.overall_mood,
                "target_era": style_guide.target_era,
                "orchestration_style": style_guide.orchestration_style,
            },
            continuity_sheet=storyboard.continuity.to_dict(),
        )

    def _collect_warnings(self, storyboard: Storyboard) -> List[str]:
        warnings: List[str] = []
        for shot in storyboard.shots:
            if not shot.continuity_anchor:
                warnings.append(f"镜头 {shot.shot_id} 缺少连续性锚点，跨镜头一致性可能受损")
            if not shot.image_prompt:
                warnings.append(f"镜头 {shot.shot_id} 缺少图像提示词")
        return warnings

    # -- 工具 ------------------------------------------------------------

    @staticmethod
    def _motion_for(movement: CameraMovement) -> VideoMotionType:
        return _CAMERA_TO_MOTION.get(movement.value, VideoMotionType.CUSTOM)

    @staticmethod
    def _art_style(preset: str) -> ArtStyle:
        return _STYLE_TO_ART.get(preset, ArtStyle.CUSTOM)

    @staticmethod
    def _default_style_guide(title: str) -> ProjectStyleGuide:
        return ProjectStyleGuide(
            project_id=f"proj_{title}",
            genre=MusicalGenre.CINEMATIC,
            overall_mood="neutral",
            target_era="contemporary",
            base_tempo_range=(80.0, 140.0),
            base_dynamics=0.5,
            reverb_character="medium_hall",
            orchestration_style="hybrid",
            mixing_balance={"voice": 0.6, "music": 0.3, "sfxs": 0.1},
            dialogue_style="natural",
        )


def _sec_to_tc(seconds: float, fps: int) -> str:
    """秒 -> SMPTE 时间码 HH:MM:SS:FF。"""
    total_frames = int(round(seconds * fps))
    ff = total_frames % fps
    total_seconds = total_frames // fps
    ss = total_seconds % 60
    mm = (total_seconds // 60) % 60
    hh = total_seconds // 3600
    return f"{hh:02d}:{mm:02d}:{ss:02d}:{ff:02d}"


def produce_from_script(
    script_text: str,
    style_guide: Optional[ProjectStyleGuide] = None,
    settings: Optional[ProductionSettings] = None,
) -> ProductionResult:
    """便捷入口：剧本文本 -> 制作结果。"""
    from src.filmmaking.script import ScreenplayParser

    screenplay = ScreenplayParser().parse(script_text)
    pipeline = FilmProductionPipeline(style_guide=style_guide, settings=settings)
    return pipeline.produce(screenplay, script_text=script_text)
