"""专业 AI 影视制作层测试。

覆盖：剧本解析、导演分镜与连续性、制作管线端到端编排、
时间线与 CMX3600 EDL 产出、成片清单序列化。
"""
import json

from src.filmmaking import (
    ContinuitySheet,
    Director,
    FilmProductionPipeline,
    ProductionManifest,
    ScreenplayParser,
    ShotSize,
    Storyboard,
    produce_from_script,
)

SAMPLE_SCRIPT = """TITLE: 星海回忆
LOGLINE: 一名宇航员在末日地球寻找最后的歌声
GENRE: 科幻

SCENE 1: 废弃实验室
INT. 废弃实验室 - 夜
林夜: 系统还在运作吗？
艾拉: 仅剩一段录音。

SCENE 2: 城市天台
EXT. 城市天台 - 黎明
林夜: 天快亮了，该走了。
"""


def test_screenplay_parser_extracts_metadata():
    screenplay = ScreenplayParser().parse(SAMPLE_SCRIPT)
    assert screenplay.title == "星海回忆"
    assert screenplay.logline.startswith("一名宇航员")
    assert screenplay.genre == "科幻"
    assert len(screenplay.scenes) == 2
    # 角色分配稳定 ASCII id，并保留中文名
    assert len(screenplay.characters) == 2
    assert {p.character_name for p in screenplay.characters.values()} == {"林夜", "艾拉"}


def test_screenplay_parser_scene_heading():
    screenplay = ScreenplayParser().parse(SAMPLE_SCRIPT)
    scene1 = screenplay.scenes[0]
    assert scene1.interior is True
    assert scene1.time_of_day == "夜"
    assert scene1.location == "废弃实验室"
    scene2 = screenplay.scenes[1]
    assert scene2.interior is False
    assert scene2.time_of_day == "黎明"


def test_director_plans_shots_and_continuity():
    screenplay = ScreenplayParser().parse(SAMPLE_SCRIPT)
    storyboard: Storyboard = Director().plan(screenplay)
    # 双人戏：建立 + 双人镜 + 正反打/反应覆盖，镜头数应多于简单 1+角色数。
    assert storyboard.screenplay.total_shots >= 6
    assert len(storyboard.shots) == storyboard.screenplay.total_shots
    # 景别应具专业多样性：建立用宽景，对话戏含过肩/近景/全景。
    sizes = {s.shot_size.value for s in storyboard.shots}
    assert "ws" in sizes
    assert "cu" in sizes
    assert "ots" in sizes
    assert "fs" in sizes
    char_id = next(k for k, v in screenplay.characters.items() if v.character_name == "林夜")
    assert storyboard.continuity.character_anchor(char_id)
    # 含角色的镜头必须把连续性锚点注入图像提示词
    char_shot = next(s for s in storyboard.shots if s.characters == [char_id])
    assert "林夜" in char_shot.image_prompt
    assert char_shot.continuity_anchor == storyboard.continuity.character_anchor(char_id)


def test_director_establishing_uses_dissolve_then_cuts():
    screenplay = ScreenplayParser().parse(SAMPLE_SCRIPT)
    storyboard = Director().plan(screenplay)
    assert storyboard.shots[0].shot_size.value == "ws"
    assert storyboard.shots[0].transition == "dissolve"
    assert all(s.transition in {"cut", "dissolve"} for s in storyboard.shots)


def test_director_establishing_shot_is_wide():
    screenplay = ScreenplayParser().parse(SAMPLE_SCRIPT)
    storyboard = Director().plan(screenplay)
    first = storyboard.shots[0]
    assert first.shot_size == ShotSize.WIDE


def test_pipeline_end_to_end_produce():
    result = produce_from_script(SAMPLE_SCRIPT)
    assert result.success is True
    assert result.shots_total >= 6
    assert result.shots_completed == result.shots_total
    assert result.duration_sec > 0
    # 时间线应挂载视频与音频资产
    assert len(result.project.timeline.tracks["video"].assets) == result.shots_total
    assert len(result.project.timeline.tracks["voice"].assets) == 2  # 两个含对白场景
    assert result.project.timeline.tracks["music"].assets
    assert result.project.timeline.tracks["sfxs"].assets
    assert result.stats["total_assets"] >= 6


def test_pipeline_xml_interchange_valid():
    import xml.etree.ElementTree as ET

    result = produce_from_script(SAMPLE_SCRIPT)
    root = ET.fromstring(result.edl_xml)
    assert root.tag == "hydraflow_interchange"
    video_track = root.find(".//track[@type='video']")
    assert video_track is not None
    assert len(video_track.findall("clip")) == result.shots_total
    audio_tracks = root.findall(".//track[@type='audio']")
    assert len(audio_tracks) == 3  # voice / music / sfxs


def test_pipeline_timeline_start_times_are_sequential():
    result = produce_from_script(SAMPLE_SCRIPT)
    starts = [a.start_time for a in result.project.timeline.tracks["video"].assets]
    assert starts == sorted(starts)
    assert starts[0] == 0.0
    # 音乐从 0 开始并覆盖整片
    music = result.project.timeline.tracks["music"].assets[0]
    assert music.start_time == 0.0
    assert music.duration == result.duration_sec


def test_pipeline_edl_includes_audio_events():
    result = produce_from_script(SAMPLE_SCRIPT)
    edl = result.edl
    assert "* AUDIO EVENTS" in edl
    assert "A     C" in edl
    # 视频事件与音频事件都应存在
    assert "001  " in edl
    assert "MUS_" in edl.upper() or "MUS_" in edl


def test_pipeline_manifest_is_serializable():
    result = produce_from_script(SAMPLE_SCRIPT)
    manifest: ProductionManifest = result.manifest
    payload = json.loads(manifest.to_json())
    assert payload["title"] == "星海回忆"
    assert payload["shot_count"] >= 6
    assert len(payload["scenes"]) == 2
    # 连续性表必须进入清单，供后端保证跨镜头一致
    assert len(payload["continuity_sheet"]["characters"]) == 2
    assert any("林夜" in value for value in payload["continuity_sheet"]["characters"].values())


def test_pipeline_edl_format():
    result = produce_from_script(SAMPLE_SCRIPT)
    edl = result.edl
    assert edl.startswith("TITLE: 星海回忆")
    assert "FCM: NON-DROP FRAME" in edl
    # 每个视频镜头生成一条 EDL 事件（至少 5 条 001..005）
    assert "001  " in edl
    assert "005  " in edl
    # 时间码格式 HH:MM:SS:FF
    assert "00:00:00:00" in edl


def test_pipeline_no_audio_when_no_dialogue():
    screenplay = ScreenplayParser().parse(SAMPLE_SCRIPT)
    # 不传 script_text 时仍应有背景音乐，但不应有对白轨
    pipeline = FilmProductionPipeline()
    result = pipeline.produce(screenplay, script_text="")
    assert result.project.timeline.tracks["music"].assets
    assert not result.project.timeline.tracks["voice"].assets


def test_continuity_sheet_roundtrip():
    sheet = ContinuitySheet()
    sheet.characters["hero"] = "蓝色战袍的战士"
    data = sheet.to_dict()
    assert data["characters"]["hero"] == "蓝色战袍的战士"
