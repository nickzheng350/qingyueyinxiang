"""影视剧本数据模型与解析。

提供专业影视制作所需的剧本结构 Screenplay -> FilmScene -> Shot，
以及镜头语言枚举（景别 / 运镜 / 焦段 / 角度 / 布光），
并附带一个与 enhanced_audio_engine.ScriptParser 兼容的轻量剧本解析器。
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from src.multimodal.enhanced_audio_engine import CharacterProfile, ProjectStyleGuide

logger = logging.getLogger("hydraflow.filmmaking.script")


class ShotSize(str, Enum):
    """景别（取景范围，由远及近）。"""

    EXTREME_WIDE = "ews"          # 大远景
    WIDE = "ws"                   # 远景
    FULL = "fs"                   # 全景
    MEDIUM = "ms"                 # 中景
    MEDIUM_CLOSEUP = "mcu"        # 中近景
    CLOSEUP = "cu"                # 近景
    BIG_CLOSEUP = "bcu"           # 大特写
    EXTREME_CLOSEUP = "ecu"       # 极特写
    POV = "pov"                   # 主观镜头
    OVER_SHOULDER = "ots"         # 过肩镜头


class CameraMovement(str, Enum):
    """运镜方式。"""

    STATIC = "static"
    PAN = "pan"
    TILT = "tilt"
    DOLLY = "dolly"
    ZOOM = "zoom"
    TRUCK = "truck"
    CRANE = "crane"
    STEADICAM = "steadicam"
    HANDHELD = "handheld"
    AERIAL = "aerial"
    FOLLOW = "follow"


class LensType(str, Enum):
    """镜头焦段。"""

    WIDE = "wide"
    STANDARD = "standard"
    TELEPHOTO = "telephoto"
    MACRO = "macro"
    FISHEYE = "fisheye"
    ANAMORPHIC = "anamorphic"


class CameraAngle(str, Enum):
    """拍摄角度。"""

    BIRD = "bird"     # 鸟瞰
    HIGH = "high"     # 俯角
    EYE = "eye"       # 平视
    LOW = "low"       # 仰角
    WORM = "worm"     # 蚂蚁视角


class LightingSetup(str, Enum):
    """布光方案。"""

    THREE_POINT = "three_point"
    LOW_KEY = "low_key"
    HIGH_KEY = "high_key"
    NATURAL = "natural"
    PRACTICAL = "practical"
    SILHOUETTE = "silhouette"
    CHIAROSCURO = "chiaroscuro"


@dataclass
class Shot:
    """镜头：影视制作的最小可视单元，也是一致性校验与渲染的原子任务。"""

    shot_id: str
    scene_id: str
    shot_number: int
    shot_size: ShotSize
    camera_movement: CameraMovement
    lens: LensType
    angle: CameraAngle
    lighting: LightingSetup
    duration_sec: float
    description: str
    image_prompt: str
    motion_prompt: str
    characters: List[str] = field(default_factory=list)
    location: str = "unknown"
    time_of_day: str = "day"
    mood: str = "neutral"
    continuity_anchor: str = ""
    style_preset: str = "cinematic"
    transition: str = "cut"
    keyframe_path: Optional[str] = None
    video_path: Optional[str] = None


@dataclass
class FilmScene:
    """场景：同一时间地点的连续镜头集合。"""

    scene_id: str
    scene_number: int
    location: str
    time_of_day: str
    mood: str
    interior: bool = True
    description: str = ""
    characters: List[str] = field(default_factory=list)
    lines: List[Dict[str, str]] = field(default_factory=list)
    shots: List[Shot] = field(default_factory=list)


@dataclass
class Screenplay:
    """剧本：整部影片的制作蓝图。"""

    title: str
    logline: str
    genre: str
    scenes: List[FilmScene] = field(default_factory=list)
    characters: Dict[str, CharacterProfile] = field(default_factory=dict)
    style_guide: Optional[ProjectStyleGuide] = None

    @property
    def total_shots(self) -> int:
        return sum(len(scene.shots) for scene in self.scenes)

    @property
    def total_duration_sec(self) -> float:
        return sum(shot.duration_sec for scene in self.scenes for shot in scene.shots)


class ScreenplayParser:
    """轻量剧本解析器。

    兼容 enhanced_audio_engine.ScriptParser 的分场标记，并额外提取
    片名 / 一句话梗概 / 类型 与场景内外、时间信息，产出 FilmScene 骨架。

    文本格式示例::

        TITLE: 星海回忆
        LOGLINE: 一名宇航员在末日地球寻找最后的歌声
        GENRE: 科幻

        SCENE 1: 废弃实验室
        INT. 废弃实验室 - 夜
        林夜: 系统还在运作吗？
        艾拉: 仅剩一段录音。

        SCENE 2: 城市天台
        EXT. 城市天台 - 黎明
        林夜: 天快亮了。
    """

    _title_re = re.compile(r"^TITLE\s*:\s*(.+)$", re.IGNORECASE)
    _logline_re = re.compile(r"^LOGLINE\s*:\s*(.+)$", re.IGNORECASE)
    _genre_re = re.compile(r"^GENRE\s*:\s*(.+)$", re.IGNORECASE)
    _scene_re = re.compile(r"^SCENE\s*(\d+)\s*:\s*(.+)$", re.IGNORECASE)
    _heading_re = re.compile(r"^(INT\.|EXT\.)\s*(.+)$", re.IGNORECASE)
    _char_re = re.compile(r"^([A-Za-z0-9_一-鿿\s]+)\s*:\s*(.+)$")

    def parse(self, text: str) -> Screenplay:
        screenplay = Screenplay(title="未命名影片", logline="", genre="剧情")
        current_scene: Optional[FilmScene] = None
        char_id_map: Dict[str, str] = {}

        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            match = self._title_re.match(line)
            if match:
                screenplay.title = match.group(1).strip()
                continue
            match = self._logline_re.match(line)
            if match:
                screenplay.logline = match.group(1).strip()
                continue
            match = self._genre_re.match(line)
            if match:
                screenplay.genre = match.group(1).strip()
                continue

            match = self._scene_re.match(line)
            if match:
                if current_scene is not None:
                    screenplay.scenes.append(current_scene)
                scene_num = int(match.group(1))
                current_scene = FilmScene(
                    scene_id=f"scene_{scene_num:03d}",
                    scene_number=scene_num,
                    location=match.group(2).strip(),
                    time_of_day="day",
                    mood="neutral",
                    description=match.group(2).strip(),
                )
                continue

            match = self._heading_re.match(line)
            if match and current_scene is not None:
                current_scene.interior = match.group(1).upper().startswith("INT")
                rest = match.group(2).strip()
                if "-" in rest:
                    location_part, _, time_part = rest.partition("-")
                    current_scene.location = location_part.strip()
                    current_scene.time_of_day = (time_part.strip() or "day")
                else:
                    current_scene.location = rest
                continue

            match = self._char_re.match(line)
            if match and current_scene is not None:
                char_name = match.group(1).strip()
                dialogue_text = match.group(2).strip()
                char_id = char_id_map.get(char_name)
                if char_id is None:
                    char_id = f"char_{len(char_id_map) + 1}"
                    char_id_map[char_name] = char_id
                    screenplay.characters[char_id] = self._default_profile(char_id, char_name)
                if char_id not in current_scene.characters:
                    current_scene.characters.append(char_id)
                current_scene.lines.append(
                    {"speaker_id": char_id, "speaker": char_name, "text": dialogue_text}
                )
                continue

        if current_scene is not None:
            screenplay.scenes.append(current_scene)
        return screenplay

    @staticmethod
    def _default_profile(char_id: str, char_name: str) -> CharacterProfile:
        from src.multimodal.enhanced_audio_engine import CharacterType

        return CharacterProfile(
            character_id=char_id,
            character_name=char_name,
            character_type=CharacterType.PROTAGONIST,
            voice_type="neutral",
            pitch_range=(-4.0, 4.0),
            base_tempo=120.0,
            base_brightness=0.5,
            base_warmth=0.5,
            speech_pattern="expressive",
        )
