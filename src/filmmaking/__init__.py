"""专业 AI 影视制作层。

将 HydraFlow 的多模态积木（图生视频 / 风格迁移 / 音频引擎 / 融合引擎）
编排为一条完整的影视生产链路：

    剧本(Screenplay) --导演--> 镜头表(Storyboard) --制作管线--> 成片清单(Manifest)
                                                                 时间线(Timeline)
                                                                 剪辑决策表(EDL)

该层定位为**影视预生产与制作编排**：负责镜头规划、跨镜头视觉连续性、
生产参数一致性校验，并产出可直接交付后期（NLE）的清单与 EDL。
实际像素/音频合成交由已注册的模型后端完成（本地为占位实现）。
"""

from src.filmmaking.script import (
    CameraAngle,
    CameraMovement,
    FilmScene,
    LensType,
    LightingSetup,
    Screenplay,
    ScreenplayParser,
    Shot,
    ShotSize,
)
from src.filmmaking.director import ContinuitySheet, Director, Storyboard
from src.filmmaking.pipeline import (
    FilmProductionPipeline,
    ProductionManifest,
    ProductionResult,
    produce_from_script,
)

__all__ = [
    "CameraAngle",
    "CameraMovement",
    "FilmScene",
    "LensType",
    "LightingSetup",
    "Screenplay",
    "ScreenplayParser",
    "Shot",
    "ShotSize",
    "ContinuitySheet",
    "Director",
    "Storyboard",
    "FilmProductionPipeline",
    "ProductionManifest",
    "ProductionResult",
    "produce_from_script",
]
