"""导演模块：将剧本分解为镜头表（Storyboard）并保证跨镜头视觉连续性。

专业影视制作的核心难点之一是**连续性（continuity）**——同一角色 / 场景
在成百上千个镜头中必须保持外观一致。Director 在进入渲染前生成一张
连续性表（ContinuitySheet），把每个角色 / 场景的规范锚点注入到对应镜头的
图像提示词中，从源头约束一致性。
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List

from src.filmmaking.script import (
    CameraAngle,
    CameraMovement,
    FilmScene,
    LensType,
    LightingSetup,
    Screenplay,
    Shot,
    ShotSize,
)

logger = logging.getLogger("hydraflow.filmmaking.director")

# 依据场景情绪选择默认运镜与布光，模拟导演的视听语言决策。
_MOOD_CAMERA: Dict[str, CameraMovement] = {
    "neutral": CameraMovement.STATIC,
    "calm": CameraMovement.STEADICAM,
    "tense": CameraMovement.HANDHELD,
    "epic": CameraMovement.CRANE,
    "chaotic": CameraMovement.HANDHELD,
    "romantic": CameraMovement.FOLLOW,
    "dark": CameraMovement.STATIC,
    "bright": CameraMovement.STATIC,
}

_MOOD_LIGHTING: Dict[str, LightingSetup] = {
    "neutral": LightingSetup.THREE_POINT,
    "calm": LightingSetup.NATURAL,
    "dark": LightingSetup.LOW_KEY,
    "bright": LightingSetup.HIGH_KEY,
    "noir": LightingSetup.CHIAROSCURO,
    "tense": LightingSetup.LOW_KEY,
}


@dataclass
class ContinuitySheet:
    """连续性表：记录角色 / 场景的跨镜头一致锚点。"""

    characters: Dict[str, str] = field(default_factory=dict)
    locations: Dict[str, str] = field(default_factory=dict)

    def character_anchor(self, character_id: str) -> str:
        return self.characters.get(character_id, "")

    def to_dict(self) -> Dict[str, Dict[str, str]]:
        return {"characters": self.characters, "locations": self.locations}


class Director:
    """导演：剧本 -> 镜头表，并维护视觉连续性。"""

    def __init__(self, default_shot_duration: float = 4.0):
        self.default_shot_duration = default_shot_duration

    def plan(self, screenplay: Screenplay) -> "Storyboard":
        continuity = self._build_continuity(screenplay)
        shots: List[Shot] = []
        shot_counter = 0
        for scene in screenplay.scenes:
            scene_shots = self._plan_scene(scene, continuity, shot_counter)
            scene.shots = scene_shots
            shots.extend(scene_shots)
            shot_counter += len(scene_shots)
        return Storyboard(screenplay=screenplay, shots=shots, continuity=continuity)

    def _build_continuity(self, screenplay: Screenplay) -> ContinuitySheet:
        sheet = ContinuitySheet()
        for char_id, profile in screenplay.characters.items():
            sheet.characters[char_id] = (
                f"{profile.character_name}，{profile.voice_type}声线，"
                f"服装与发型在全部镜头中保持统一"
            )
        for scene in screenplay.scenes:
            sheet.locations[scene.scene_id] = (
                f"{scene.location}，{scene.time_of_day}，"
                f"{'室内' if scene.interior else '室外'}"
            )
        return sheet

    def _plan_scene(
        self, scene: FilmScene, continuity: ContinuitySheet, start_index: int
    ) -> List[Shot]:
        shots: List[Shot] = []
        mood = scene.mood.lower()
        establishing = Shot(
            shot_id=f"{scene.scene_id}_s{start_index:03d}",
            scene_id=scene.scene_id,
            shot_number=start_index,
            shot_size=ShotSize.WIDE,
            camera_movement=CameraMovement.STATIC,
            lens=LensType.ANAMORPHIC,
            angle=CameraAngle.EYE,
            lighting=self._lighting_for(mood),
            duration_sec=self.default_shot_duration * 1.5,
            description=f"建立镜头：{scene.description}",
            image_prompt=self._image_prompt(scene, None, continuity, "宽景展现环境全貌"),
            motion_prompt="缓慢推进，建立场景空间关系",
            characters=list(scene.characters),
            location=scene.location,
            time_of_day=scene.time_of_day,
            mood=scene.mood,
            continuity_anchor=continuity.locations.get(scene.scene_id, ""),
        )
        shots.append(establishing)

        for offset, char_id in enumerate(scene.characters, start=1):
            shot = Shot(
                shot_id=f"{scene.scene_id}_s{start_index + offset:03d}",
                scene_id=scene.scene_id,
                shot_number=start_index + offset,
                shot_size=ShotSize.MEDIUM,
                camera_movement=self._camera_for(mood),
                lens=LensType.STANDARD,
                angle=CameraAngle.EYE,
                lighting=self._lighting_for(mood),
                duration_sec=self.default_shot_duration,
                description=f"{char_id} 的对话 / 反应镜头",
                image_prompt=self._image_prompt(scene, char_id, continuity, "中景人物"),
                motion_prompt="轻微运镜保持人物主体稳定",
                characters=[char_id],
                location=scene.location,
                time_of_day=scene.time_of_day,
                mood=scene.mood,
                continuity_anchor=continuity.character_anchor(char_id),
            )
            shots.append(shot)
        return shots

    def _image_prompt(
        self,
        scene: FilmScene,
        char_id: Any,
        continuity: ContinuitySheet,
        framing: str,
    ) -> str:
        parts = [
            f"{scene.mood}氛围的{scene.location}",
            f"{scene.time_of_day}光线",
            framing,
        ]
        if char_id:
            anchor = continuity.character_anchor(str(char_id))
            if anchor:
                parts.append(f"人物：{anchor}")
        return "，".join(parts)

    @staticmethod
    def _camera_for(mood: str) -> CameraMovement:
        return _MOOD_CAMERA.get(mood, CameraMovement.STATIC)

    @staticmethod
    def _lighting_for(mood: str) -> LightingSetup:
        return _MOOD_LIGHTING.get(mood, LightingSetup.THREE_POINT)


@dataclass
class Storyboard:
    """镜头表：导演对整部影片的视觉规划，是制作管线的输入。"""

    screenplay: Screenplay
    shots: List[Shot] = field(default_factory=list)
    continuity: ContinuitySheet = field(default_factory=ContinuitySheet)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.screenplay.title,
            "shot_count": len(self.shots),
            "total_duration_sec": self.screenplay.total_duration_sec,
            "continuity": self.continuity.to_dict(),
            "shots": [
                {
                    "shot_id": shot.shot_id,
                    "scene_id": shot.scene_id,
                    "shot_size": shot.shot_size.value,
                    "camera_movement": shot.camera_movement.value,
                    "lens": shot.lens.value,
                    "angle": shot.angle.value,
                    "lighting": shot.lighting.value,
                    "duration_sec": shot.duration_sec,
                    "image_prompt": shot.image_prompt,
                    "motion_prompt": shot.motion_prompt,
                    "continuity_anchor": shot.continuity_anchor,
                    "characters": shot.characters,
                }
                for shot in self.shots
            ],
        }
