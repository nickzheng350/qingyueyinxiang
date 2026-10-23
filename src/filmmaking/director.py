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

# 情绪 -> 拍摄角度（英雄感低角度、脆弱 / 紧张高角度、史诗鸟瞰）。
_MOOD_ANGLE: Dict[str, CameraAngle] = {
    "heroic": CameraAngle.LOW,
    "tense": CameraAngle.HIGH,
    "vulnerable": CameraAngle.HIGH,
    "epic": CameraAngle.BIRD,
}

# 运镜 -> 默认运动提示词。
_MOTION_PROMPT: Dict[str, str] = {
    "static": "固定机位，构图稳定",
    "pan": "水平摇摄",
    "tilt": "垂直摇摄",
    "dolly": "缓慢推拉，改变透视",
    "zoom": "变焦推近/拉远",
    "truck": "横移跟拍",
    "crane": "升降运动，展现场面",
    "steadicam": "斯坦尼康平滑跟随",
    "handheld": "手持呼吸感，增强临场",
    "aerial": "航拍俯瞰",
    "follow": "跟拍人物移动",
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
    """导演：剧本 -> 镜头表，并维护视觉连续性。

    调度遵循专业影视的镜头覆盖（coverage）原则：每场先拍建立镜头，
    双人戏采用"正反打 + 双人镜 + 反应特写"的经典调度，单人戏补充中景 / 近景，
    并按情绪选择角度与运镜、在镜头出点标注转场。
    """

    def __init__(self, default_shot_duration: float = 4.0, max_dialogue_beats: int = 3):
        self.default_shot_duration = default_shot_duration
        self.max_dialogue_beats = max_dialogue_beats

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
        base = self.default_shot_duration
        idx = start_index

        # 1) 建立镜头：宽景交代时间 / 地点 / 环境
        shots.append(
            self._make_shot(
                scene, continuity, idx, ShotSize.WIDE, CameraMovement.STATIC,
                LensType.ANAMORPHIC, CameraAngle.EYE, base * 1.5,
                "建立镜头：交代环境", "宽景展现环境全貌",
                list(scene.characters), "dissolve",
            )
        )
        idx += 1

        # 2) 双人戏：双人镜 + 正反打 + 反应特写
        if len(scene.characters) >= 2 and scene.lines:
            lead, support = scene.characters[0], scene.characters[1]
            shots.append(
                self._make_shot(
                    scene, continuity, idx, ShotSize.FULL, CameraMovement.STATIC,
                    LensType.STANDARD, CameraAngle.EYE, base,
                    "双人镜头：确立人物关系", "全景收两人同框",
                    [lead, support], "cut",
                )
            )
            idx += 1
            for beat in scene.lines[: self.max_dialogue_beats]:
                speaker_id = beat["speaker_id"]
                speaker = lead if speaker_id == lead else support
                listener = support if speaker_id == lead else lead
                # 过肩：拍说话者，听者入前景
                shots.append(
                    self._make_shot(
                        scene, continuity, idx, ShotSize.OVER_SHOULDER, CameraMovement.STATIC,
                        LensType.TELEPHOTO, CameraAngle.EYE, base,
                        f"过肩：{speaker} 台词", "过肩构图突出说话者、听者前景",
                        [speaker, listener], "cut",
                    )
                )
                idx += 1
                # 听者反应近景（推近强调情绪）
                shots.append(
                    self._make_shot(
                        scene, continuity, idx, ShotSize.CLOSEUP, CameraMovement.DOLLY,
                        LensType.TELEPHOTO, self._angle_for(mood), base,
                        f"反应：{listener} 倾听", "近景推近反应",
                        [listener], "cut",
                    )
                )
                idx += 1

        # 3) 单人戏：中景 + 近景覆盖
        elif len(scene.characters) == 1:
            char_id = scene.characters[0]
            shots.append(
                self._make_shot(
                    scene, continuity, idx, ShotSize.MEDIUM, self._camera_for(mood),
                    LensType.STANDARD, CameraAngle.EYE, base,
                    f"{char_id} 中景", "中景人物",
                    [char_id], "cut",
                )
            )
            idx += 1
            shots.append(
                self._make_shot(
                    scene, continuity, idx, ShotSize.CLOSEUP, CameraMovement.DOLLY,
                    LensType.TELEPHOTO, self._angle_for(mood), base,
                    f"{char_id} 近景", "近景强调",
                    [char_id], "cut",
                )
            )
            idx += 1

        return shots

    def _make_shot(
        self,
        scene: FilmScene,
        continuity: ContinuitySheet,
        idx: int,
        size: ShotSize,
        move: CameraMovement,
        lens: LensType,
        angle: CameraAngle,
        dur: float,
        desc: str,
        framing: str,
        chars: List[str],
        trans: str,
    ) -> Shot:
        anchor_char = chars[0] if chars else None
        if anchor_char:
            continuity_anchor = continuity.character_anchor(anchor_char)
        else:
            continuity_anchor = continuity.locations.get(scene.scene_id, "")
        return Shot(
            shot_id=f"{scene.scene_id}_s{idx:03d}",
            scene_id=scene.scene_id,
            shot_number=idx,
            shot_size=size,
            camera_movement=move,
            lens=lens,
            angle=angle,
            lighting=self._lighting_for(scene.mood.lower()),
            duration_sec=dur,
            description=desc,
            image_prompt=self._image_prompt(scene, anchor_char, continuity, framing),
            motion_prompt=self._default_motion(move),
            characters=list(chars),
            location=scene.location,
            time_of_day=scene.time_of_day,
            mood=scene.mood,
            continuity_anchor=continuity_anchor,
            transition=trans,
        )

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

    @staticmethod
    def _angle_for(mood: str) -> CameraAngle:
        return _MOOD_ANGLE.get(mood, CameraAngle.EYE)

    @staticmethod
    def _default_motion(move: CameraMovement) -> str:
        return _MOTION_PROMPT.get(move.value, "固定机位")


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
                    "transition": shot.transition,
                    "characters": shot.characters,
                }
                for shot in self.shots
            ],
        }
