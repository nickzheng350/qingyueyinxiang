"""提示词库 - 细粒度分类与多维维度"""
import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Set, Union
from enum import Enum
from collections import defaultdict
import json

logger = logging.getLogger("hydraflow.core.prompt_library")


class PromptCategory(str, Enum):
    """提示词大类"""
    STYLE = "style"  # 风格
    CONTENT = "content"  # 内容
    OBJECT = "object"  # 对象
    QUALITY = "quality"  # 质量
    COMPOSITION = "composition"  # 构图
    LIGHTING = "lighting"  # 光线
    ATMOSPHERE = "atmosphere"  # 氛围
    CAMERA = "camera"  # 相机设置
    COLOR = "color"  # 色彩
    ARTIST = "artist"  # 艺术家风格


class FineStyle(str, Enum):
    """细粒度风格"""
    # 绘画风格
    IMPRESSIONISM = "impressionism"  # 印象派
    SURREALISM = "surrealism"  # 超现实主义
    CUBISM = "cubism"  # 立体主义
    ABSTRACT = "abstract"  # 抽象
    REALISM = "realism"  # 现实主义
    POP_ART = "pop_art"  # 波普艺术
    ART_DECO = "art_deco"  # 装饰艺术
    
    # 动漫风格
    MANGA = "manga"  # 漫画
    ANIME = "anime"  # 动漫
    STUDIO_GHIBLI = "studio_ghibli"  # 吉卜力
    MAKOTO_SHINKAI = "makoto_shinkai"  # 新海诚
    
    # 现代风格
    CYBERPUNK = "cyberpunk"  # 赛博朋克
    STEAMPUNK = "steampunk"  # 蒸汽朋克
    DIEPUNK = "diepunk"  # 柴油朋克
    SOLARPUNK = "solarpunk"  # 太阳朋克
    
    # 摄影风格
    PHOTOREALISTIC = "photorealistic"  # 写实摄影
    PORTRAIT = "portrait"  # 人像摄影
    LANDSCAPE = "landscape"  # 风景摄影
    STREET = "street"  # 街拍
    FINE_ART = "fine_art"  # 艺术摄影
    
    # 特殊风格
    WATERCOLOR = "watercolor"  # 水彩
    OIL_PAINTING = "oil_painting"  # 油画
    CHINESE_INK = "chinese_ink"  # 国画
    PIXEL_ART = "pixel_art"  # 像素艺术
    VECTOR = "vector"  # 矢量
    THREED_RENDER = "3d_render"  # 3D渲染


class FineContent(str, Enum):
    """细粒度内容"""
    # 场景
    URBAN = "urban"  # 城市
    NATURE = "nature"  # 自然
    LANDSCAPE = "landscape"  # 风景
    SEASCAPE = "seascape"  # 海景
    MOUNTAIN = "mountain"  # 山景
    FOREST = "forest"  # 森林
    DESERT = "desert"  # 沙漠
    OCEAN = "ocean"  # 海洋
    
    # 人物
    HUMAN = "human"  # 人类
    PORTRAIT = "portrait"  # 肖像
    FANTASY = "fantasy"  # 奇幻
    SUPERHERO = "superhero"  # 超级英雄
    ANIME_CHARACTER = "anime_character"  # 动漫角色
    
    # 物体
    VEHICLE = "vehicle"  # 交通工具
    ANIMAL = "animal"  # 动物
    BUILDING = "building"  # 建筑
    FURNITURE = "furniture"  # 家具
    FOOD = "food"  # 食物
    
    # 特殊
    ABSTRACT_PATTERN = "abstract_pattern"  # 抽象图案
    TEXT = "text"  # 文字
    LOGO = "logo"  # 标志


class FineQuality(str, Enum):
    """细粒度质量"""
    # 基础质量
    LOW = "low"
    STANDARD = "standard"
    HIGH = "high"
    ULTRA = "ultra"
    MASTERPIECE = "masterpiece"
    
    # 质量细节
    HIGH_DETAIL = "high_detail"
    ULTRA_DETAIL = "ultra_detail"
    CLEAR = "clear"
    SHARP = "sharp"
    IN_FOCUS = "in_focus"
    
    # 专业质量
    PROFESSIONAL = "professional"
    AWARD_WINNING = "award_winning"
    ART_GALLERY = "art_gallery"
    MUSEUM_QUALITY = "museum_quality"
    
    # 分辨率
    HD = "hd"
    FULL_HD = "full_hd"
    TWO_K = "2k"
    FOUR_K = "4k"
    EIGHT_K = "8k"
    SIXTEEN_K = "16k"


class FineLighting(str, Enum):
    """细粒度光线"""
    # 光源类型
    NATURAL = "natural"
    SUNLIGHT = "sunlight"
    MOONLIGHT = "moonlight"
    ARTIFICIAL = "artificial"
    GOLDEN_HOUR = "golden_hour"
    BLUE_HOUR = "blue_hour"
    SUNRISE = "sunrise"
    SUNSET = "sunset"
    
    # 光效
    SOFT = "soft"
    HARD = "hard"
    RIM = "rim"
    BACKLIGHT = "backlight"
    KEY_LIGHT = "key_light"
    FILL_LIGHT = "fill_light"
    NEON = "neon"
    BIOLUMINESCENCE = "bioluminescence"
    
    # 氛围光
    DRAMATIC = "dramatic"
    MOOD = "mood"
    MYSTERIOUS = "mysterious"
    WARM = "warm"
    COOL = "cool"
    CINEMATIC = "cinematic"


class FineAtmosphere(str, Enum):
    """细粒度氛围"""
    EMOTIONAL = "emotional"
    DRAMATIC = "dramatic"
    PEACEFUL = "peaceful"
    TENSE = "tense"
    HAPPY = "happy"
    MELANCHOLIC = "melancholic"
    EXCITING = "exciting"
    MYSTERIOUS = "mysterious"
    MAGICAL = "magical"
    SCARY = "scary"
    COZY = "cozy"
    ENERGETIC = "energetic"


class FineCamera(str, Enum):
    """细粒度相机设置"""
    # 视角
    CLOSE_UP = "close_up"
    MEDIUM_SHOT = "medium_shot"
    WIDE_SHOT = "wide_shot"
    EXTREME_WIDE = "extreme_wide"
    AERIAL = "aerial"
    BIRDSEYE = "birdseye"
    WORMSEYE = "wormseye"
    
    # 镜头类型
    TELEPHOTO = "telephoto"
    FISHEYE = "fisheye"
    WIDE_ANGLE = "wide_angle"
    MACRO = "macro"
    
    # 技术参数
    BOKEH = "bokeh"
    SHALLOW_DEPTH = "shallow_depth_of_field"
    LONG_EXPOSURE = "long_exposure"
    LOW_SHUTTER = "low_shutter"
    HIGH_SHUTTER = "high_shutter"
    F_NUM = "f_num"


class FineColor(str, Enum):
    """细粒度色彩"""
    # 色彩方案
    VIBRANT = "vibrant"
    PASTEL = "pastel"
    MUTED = "muted"
    WARM = "warm"
    COOL = "cool"
    MONOCHROME = "monochrome"
    BLACK_AND_WHITE = "black_and_white"
    HIGH_CONTRAST = "high_contrast"
    LOW_CONTRAST = "low_contrast"
    COLOR_GRADED = "color_graded"


class FineArtist(str, Enum):
    """细粒度艺术家风格"""
    VAN_GOGH = "van_gogh"
    MONET = "monet"
    PICASSO = "picasso"
    DALI = "dali"
    HOKUSAI = "hokusai"
    MIYAZAKI = "hayao_miyazaki"
    ANSEL_ADAMS = "ansel_adams"


@dataclass
class PromptComponent:
    """提示词组件（细粒度）"""
    id: str
    category: PromptCategory
    fine_type: Optional[Union[FineStyle, FineContent, FineQuality, FineLighting, FineAtmosphere, FineCamera, FineColor, FineArtist]]
    text: str
    weight: float = 1.0
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PromptTemplate:
    """提示词模板"""
    id: str
    name: str
    description: str
    components: List[PromptComponent] = field(default_factory=list)
    required: Set[str] = field(default_factory=set)
    optional: Set[str] = field(default_factory=set)
    tags: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)


class StyleLibrary:
    """风格库"""
    
    def __init__(self):
        self.styles: Dict[FineStyle, List[str]] = {
            FineStyle.IMPRESSIONISM: ["impressionist", "impressionism", "Claude Monet style"],
            FineStyle.SURREALISM: ["surrealist", "surrealism", "Salvador Dali style"],
            FineStyle.CYBERPUNK: ["cyberpunk", "neon lights", "dystopian future"],
            FineStyle.STEAMPUNK: ["steampunk", "victorian", "brass gears"],
            FineStyle.PHOTOREALISTIC: ["photorealistic", "realistic", "photograph"],
            FineStyle.MANGA: ["manga style", "anime style", "japanese comic"],
            FineStyle.WATERCOLOR: ["watercolor painting", "watercolor style"],
            FineStyle.OIL_PAINTING: ["oil painting", "oil on canvas"],
            FineStyle.CHINESE_INK: ["chinese ink", "ink wash"],
            FineStyle.PIXEL_ART: ["pixel art", "pixelated", "retro"],
            FineStyle.ANIME: ["anime style", "anime artwork"],
            FineStyle.STUDIO_GHIBLI: ["Studio Ghibli style", "Hayao Miyazaki style"],
            FineStyle.MAKOTO_SHINKAI: ["Makoto Shinkai style"],
        }
    
    def get(self, style: FineStyle) -> List[str]:
        """获取风格提示词"""
        return self.styles.get(style, [])
    
    def get_all(self) -> List[PromptComponent]:
        """获取所有风格组件"""
        return [
            PromptComponent(
                id=f"style_{s.value}",
                category=PromptCategory.STYLE,
                fine_type=s,
                text=" ".join(texts),
                weight=1.5,
                tags=["style", s.value],
            )
            for s, texts in self.styles.items()
        ]


class ContentLibrary:
    """内容库"""
    
    def __init__(self):
        self.contents: Dict[FineContent, List[str]] = {
            FineContent.URBAN: ["city", "urban", "metropolis", "downtown"],
            FineContent.NATURE: ["nature", "outdoors", "natural"],
            FineContent.LANDSCAPE: ["landscape", "scenery", "beautiful view"],
            FineContent.FOREST: ["forest", "trees", "woods"],
            FineContent.MOUNTAIN: ["mountain", "mountain range", "peaks"],
            FineContent.OCEAN: ["ocean", "sea", "waves"],
            FineContent.HUMAN: ["human", "person", "people"],
            FineContent.PORTRAIT: ["portrait", "face", "headshot"],
            FineContent.FANTASY: ["fantasy", "magical", "mythical"],
        }
    
    def get(self, content: FineContent) -> List[str]:
        """获取内容提示词"""
        return self.contents.get(content, [])
    
    def get_all(self) -> List[PromptComponent]:
        """获取所有内容组件"""
        return [
            PromptComponent(
                id=f"content_{c.value}",
                category=PromptCategory.CONTENT,
                fine_type=c,
                text=" ".join(texts),
                weight=1.0,
                tags=["content", c.value],
            )
            for c, texts in self.contents.items()
        ]


class QualityLibrary:
    """质量库"""
    
    def __init__(self):
        self.qualities: Dict[FineQuality, List[str]] = {
            FineQuality.LOW: ["low quality", "simple"],
            FineQuality.STANDARD: ["standard", "normal quality"],
            FineQuality.HIGH: ["high quality", "detailed"],
            FineQuality.ULTRA: ["ultra detailed", "very detailed"],
            FineQuality.MASTERPIECE: ["masterpiece", "best quality", "perfect"],
            FineQuality.FOUR_K: ["4k", "high resolution"],
            FineQuality.EIGHT_K: ["8k", "ultra high resolution"],
            FineQuality.PROFESSIONAL: ["professional", "professional quality"],
        }
    
    def get(self, quality: FineQuality) -> List[str]:
        """获取质量提示词"""
        return self.qualities.get(quality, [])
    
    def get_all(self) -> List[PromptComponent]:
        """获取所有质量组件"""
        return [
            PromptComponent(
                id=f"quality_{q.value}",
                category=PromptCategory.QUALITY,
                fine_type=q,
                text=" ".join(texts),
                weight=1.5,
                tags=["quality", q.value],
            )
            for q, texts in self.qualities.items()
        ]


class LightingLibrary:
    """光线库"""
    
    def __init__(self):
        self.lightings: Dict[FineLighting, List[str]] = {
            FineLighting.GOLDEN_HOUR: ["golden hour", "sunset light"],
            FineLighting.CINEMATIC: ["cinematic lighting", "movie lighting"],
            FineLighting.NATURAL: ["natural light", "daylight"],
            FineLighting.NEON: ["neon lights", "neon"],
            FineLighting.SOFT: ["soft lighting", "diffused light"],
            FineLighting.DRAMATIC: ["dramatic lighting", "moody"],
        }
    
    def get(self, lighting: FineLighting) -> List[str]:
        """获取光线提示词"""
        return self.lightings.get(lighting, [])
    
    def get_all(self) -> List[PromptComponent]:
        """获取所有光线组件"""
        return [
            PromptComponent(
                id=f"lighting_{l.value}",
                category=PromptCategory.LIGHTING,
                fine_type=l,
                text=" ".join(texts),
                weight=1.2,
                tags=["lighting", l.value],
            )
            for l, texts in self.lightings.items()
        ]


class PromptLibrary:
    """完整提示词库"""
    
    def __init__(self):
        self.style_lib = StyleLibrary()
        self.content_lib = ContentLibrary()
        self.quality_lib = QualityLibrary()
        self.lighting_lib = LightingLibrary()
        
        self.templates: Dict[str, PromptTemplate] = {}
        self._init_default_templates()
        
        self.components_cache: Dict[PromptCategory, List[PromptComponent]] = {}
        self._init_components_cache()
    
    def _init_components_cache(self):
        """初始化组件缓存"""
        self.components_cache = {
            PromptCategory.STYLE: self.style_lib.get_all(),
            PromptCategory.CONTENT: self.content_lib.get_all(),
            PromptCategory.QUALITY: self.quality_lib.get_all(),
            PromptCategory.LIGHTING: self.lighting_lib.get_all(),
        }
    
    def _init_default_templates(self):
        """初始化默认模板"""
        # 艺术创作模板
        art_template = PromptTemplate(
            id="art_creation",
            name="Art Creation",
            description="通用艺术创作模板",
            required={"content", "style"},
            optional={"quality", "lighting", "atmosphere"},
            tags=["general", "art"],
            examples=[
                "A beautiful landscape, Studio Ghibli style, masterpiece, best quality, golden hour lighting",
            ],
        )
        self.templates[art_template.id] = art_template
        
        # 肖像摄影模板
        portrait_template = PromptTemplate(
            id="portrait_photography",
            name="Portrait Photography",
            description="专业人像摄影模板",
            required={"content", "style"},
            optional={"quality", "lighting", "camera"},
            tags=["portrait", "photography"],
            examples=[
                "A portrait of a person, photorealistic, masterpiece, 8k, soft lighting, shallow depth of field",
            ],
        )
        self.templates[portrait_template.id] = portrait_template
        
        # 赛博朋克模板
        cyberpunk_template = PromptTemplate(
            id="cyberpunk",
            name="Cyberpunk Scene",
            description="赛博朋克风格场景",
            required={"content", "style"},
            optional={"quality", "lighting", "atmosphere"},
            tags=["cyberpunk", "scifi"],
            examples=[
                "A cyberpunk city at night, neon lights, photorealistic, masterpiece, 8k, dramatic lighting",
            ],
        )
        self.templates[cyberpunk_template.id] = cyberpunk_template
    
    def get_components_by_category(self, category: PromptCategory) -> List[PromptComponent]:
        """按类别获取组件"""
        return self.components_cache.get(category, [])
    
    def get_template(self, template_id: str) -> Optional[PromptTemplate]:
        """获取模板"""
        return self.templates.get(template_id)
    
    def get_all_templates(self) -> List[PromptTemplate]:
        """获取所有模板"""
        return list(self.templates.values())
    
    def register_template(self, template: PromptTemplate):
        """注册新模板"""
        self.templates[template.id] = template
        logger.info(f"Template registered: {template.name}")
    
    def build_prompt(
        self,
        template_id: str,
        content: str,
        style: FineStyle,
        quality: FineQuality = FineQuality.HIGH,
        lighting: Optional[FineLighting] = None,
        custom_components: Optional[List[PromptComponent]] = None,
    ) -> str:
        """构建完整提示词"""
        template = self.get_template(template_id)
        if not template:
            template = self.get_template("art_creation")
        
        prompt_parts = [content]
        
        # 风格
        if style:
            prompt_parts.extend(self.style_lib.get(style))
        
        # 质量
        if quality:
            prompt_parts.extend(self.quality_lib.get(quality))
        
        # 光线
        if lighting:
            prompt_parts.extend(self.lighting_lib.get(lighting))
        
        # 自定义组件
        if custom_components:
            for comp in custom_components:
                prompt_parts.append(comp.text)
        
        return ", ".join(prompt_parts)
    
    def export_to_json(self) -> str:
        """导出为JSON"""
        data = {
            "templates": [
                {
                    "id": t.id,
                    "name": t.name,
                    "description": t.description,
                    "examples": t.examples,
                }
                for t in self.get_all_templates()
            ],
            "categories": [c.value for c in PromptCategory],
            "fine_styles": [s.value for s in FineStyle],
            "fine_content": [c.value for c in FineContent],
            "fine_quality": [q.value for q in FineQuality],
            "fine_lighting": [l.value for l in FineLighting],
            "fine_atmosphere": [a.value for a in FineAtmosphere],
            "fine_camera": [c.value for c in FineCamera],
            "fine_color": [c.value for c in FineColor],
        }
        return json.dumps(data, ensure_ascii=False, indent=2)


class MultiDimensionalEngine:
    """多维引擎（维度完整）"""
    
    def __init__(self):
        self.prompt_lib = PromptLibrary()
        
        # 维度定义
        self.dimensions = {
            "style": PromptCategory.STYLE,
            "content": PromptCategory.CONTENT,
            "quality": PromptCategory.QUALITY,
            "lighting": PromptCategory.LIGHTING,
            "atmosphere": PromptCategory.ATMOSPHERE,
            "camera": PromptCategory.CAMERA,
            "color": PromptCategory.COLOR,
            "artist": PromptCategory.ARTIST,
            "composition": PromptCategory.COMPOSITION,
        }
    
    def generate_with_dimensions(
        self,
        content: str,
        style: FineStyle = FineStyle.PHOTOREALISTIC,
        quality: FineQuality = FineQuality.HIGH,
        lighting: Optional[FineLighting] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """使用多维引擎生成"""
        prompt = self.prompt_lib.build_prompt(
            template_id="art_creation",
            content=content,
            style=style,
            quality=quality,
            lighting=lighting,
        )
        
        return {
            "prompt": prompt,
            "dimensions": {
                "content": content,
                "style": style.value,
                "quality": quality.value,
                "lighting": lighting.value if lighting else None,
            },
        }
    
    def get_available_dimensions(self) -> Dict[str, List[str]]:
        """获取可用维度"""
        return {
            "styles": [s.value for s in FineStyle],
            "contents": [c.value for c in FineContent],
            "qualities": [q.value for q in FineQuality],
            "lightings": [l.value for l in FineLighting],
            "atmospheres": [a.value for a in FineAtmosphere],
            "cameras": [c.value for c in FineCamera],
            "colors": [c.value for c in FineColor],
        }


def get_prompt_library() -> PromptLibrary:
    """获取提示词库实例"""
    return PromptLibrary()


def get_multi_dimensional_engine() -> MultiDimensionalEngine:
    """获取多维引擎实例"""
    return MultiDimensionalEngine()
