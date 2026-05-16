"""深度学习提示词优化 - 基于LLM的提示词自动优化"""
import asyncio
import logging
import time
import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from abc import ABC, abstractmethod

logger = logging.getLogger("hydraflow.deep_prompt_optimizer")


class PromptStyle(Enum):
    """提示词风格"""
    DETAILED = "detailed"
    CONCISE = "concise"
    CREATIVE = "creative"
    TECHNICAL = "technical"
    ARTISTIC = "artistic"


class TaskDomain(Enum):
    """任务领域"""
    TEXT_GENERATION = "text_generation"
    IMAGE_GENERATION = "image_generation"
    VIDEO_GENERATION = "video_generation"
    AUDIO_GENERATION = "audio_generation"
    CODE_GENERATION = "code_generation"
    MULTIMODAL = "multimodal"


@dataclass
class PromptTemplate:
    """提示词模板"""
    template_id: str
    name: str
    domain: TaskDomain
    style: PromptStyle
    template: str
    variables: List[str]
    examples: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OptimizationResult:
    """优化结果"""
    original_prompt: str
    optimized_prompt: str
    improvements: List[str] = field(default_factory=list)
    confidence: float = 0.0
    suggested_style: Optional[PromptStyle] = None
    estimated_quality_gain: float = 0.0


class BasePromptOptimizer(ABC):
    """提示词优化器基类"""

    @abstractmethod
    async def optimize(
        self,
        prompt: str,
        domain: TaskDomain,
        style: PromptStyle = None,
        context: Dict[str, Any] = None
    ) -> OptimizationResult:
        """优化提示词"""
        pass


class RuleBasedOptimizer(BasePromptOptimizer):
    """基于规则的提示词优化器"""

    def __init__(self):
        self.quality_rules = [
            ("Add specific details", self._add_details),
            ("Use clear structure", self._improve_structure),
            ("Include constraints", self._add_constraints),
            ("Specify output format", self._specify_format),
        ]

    async def optimize(
        self,
        prompt: str,
        domain: TaskDomain,
        style: PromptStyle = None,
        context: Dict[str, Any] = None
    ) -> OptimizationResult:
        """基于规则优化提示词"""
        optimized = prompt
        improvements = []

        for rule_name, rule_func in self.quality_rules:
            new_prompt = rule_func(optimized, domain, style)
            if new_prompt != optimized:
                improvements.append(rule_name)
                optimized = new_prompt

        return OptimizationResult(
            original_prompt=prompt,
            optimized_prompt=optimized,
            improvements=improvements,
            confidence=0.6,
            estimated_quality_gain=0.15,
        )

    def _add_details(self, prompt: str, domain: TaskDomain, style: PromptStyle) -> str:
        """添加细节"""
        if len(prompt) < 50:
            return prompt + " Please provide detailed and comprehensive output."
        return prompt

    def _improve_structure(self, prompt: str, domain: TaskDomain, style: PromptStyle) -> str:
        """改进结构"""
        if "structured" not in prompt.lower() and "format" not in prompt.lower():
            if domain == TaskDomain.TEXT_GENERATION:
                return prompt + " Please structure your response with clear sections."
        return prompt

    def _add_constraints(self, prompt: str, domain: TaskDomain, style: PromptStyle) -> str:
        """添加约束"""
        if "limit" not in prompt.lower() and "constraint" not in prompt.lower():
            return prompt + " Ensure the output meets the specified requirements."
        return prompt

    def _specify_format(self, prompt: str, domain: TaskDomain, style: PromptStyle) -> str:
        """指定格式"""
        if "format" not in prompt.lower() and "output" not in prompt.lower():
            return prompt + " Output the result in a clear, well-organized format."
        return prompt


class LLMBasedOptimizer(BasePromptOptimizer):
    """基于LLM的提示词优化器"""

    def __init__(self, model_name: str = "gpt-4"):
        self.model_name = model_name
        self._client = None

    async def optimize(
        self,
        prompt: str,
        domain: TaskDomain,
        style: PromptStyle = None,
        context: Dict[str, Any] = None
    ) -> OptimizationResult:
        """使用LLM优化提示词"""
        try:
            optimized = await self._call_llm(prompt, domain, style, context)

            improvements = []
            if optimized != prompt:
                improvements.append("LLM semantic enhancement")
                improvements.append("Context-aware optimization")

            return OptimizationResult(
                original_prompt=prompt,
                optimized_prompt=optimized,
                improvements=improvements,
                confidence=0.85,
                suggested_style=style,
                estimated_quality_gain=0.25,
            )

        except Exception as e:
            logger.error(f"LLM optimization failed: {e}")
            return OptimizationResult(
                original_prompt=prompt,
                optimized_prompt=prompt,
                improvements=[],
                confidence=0.0,
            )

    async def _call_llm(
        self,
        prompt: str,
        domain: TaskDomain,
        style: PromptStyle,
        context: Dict[str, Any]
    ) -> str:
        """调用LLM API（简化实现）"""
        await asyncio.sleep(0.1)

        style_guide = ""
        if style == PromptStyle.DETAILED:
            style_guide = "Provide a highly detailed and comprehensive response."
        elif style == PromptStyle.CONCISE:
            style_guide = "Keep the response brief and to the point."
        elif style == PromptStyle.CREATIVE:
            style_guide = "Use creative and imaginative language."
        elif style == PromptStyle.TECHNICAL:
            style_guide = "Use precise technical terminology."

        domain_guide = f"This is a {domain.value} task."

        return f"{prompt}\n\n{domain_guide} {style_guide}"


class HybridPromptOptimizer:
    """混合提示词优化器 - 结合规则和LLM"""

    def __init__(self, use_llm: bool = True):
        self.rule_optimizer = RuleBasedOptimizer()
        self.llm_optimizer = LLMBasedOptimizer() if use_llm else None
        self.cache: Dict[str, OptimizationResult] = {}
        self.cache_hits = 0
        self.cache_misses = 0

    def _get_cache_key(self, prompt: str, domain: TaskDomain, style: PromptStyle) -> str:
        """生成缓存键"""
        key_string = f"{prompt}:{domain.value}:{style.value if style else 'none'}"
        return hashlib.md5(key_string.encode()).hexdigest()

    async def optimize(
        self,
        prompt: str,
        domain: TaskDomain,
        style: PromptStyle = None,
        context: Dict[str, Any] = None
    ) -> OptimizationResult:
        """优化提示词"""
        cache_key = self._get_cache_key(prompt, domain, style)

        if cache_key in self.cache:
            self.cache_hits += 1
            logger.debug(f"Cache hit for prompt optimization")
            return self.cache[cache_key]

        self.cache_misses += 1

        if self.llm_optimizer:
            result = await self.llm_optimizer.optimize(prompt, domain, style, context)
        else:
            result = await self.rule_optimizer.optimize(prompt, domain, style, context)

        if len(self.cache) < 1000:
            self.cache[cache_key] = result

        return result

    def get_cache_stats(self) -> Dict[str, int]:
        """获取缓存统计"""
        return {
            "hits": self.cache_hits,
            "misses": self.cache_misses,
            "size": len(self.cache),
            "hit_rate": self.cache_hits / max(1, self.cache_hits + self.cache_misses),
        }


class PromptTemplateManager:
    """提示词模板管理器"""

    def __init__(self):
        self.templates: Dict[str, PromptTemplate] = {}
        self._load_default_templates()

    def _load_default_templates(self):
        """加载默认模板"""
        default_templates = [
            PromptTemplate(
                template_id="tpl_img_detailed",
                name="Detailed Image Generation",
                domain=TaskDomain.IMAGE_GENERATION,
                style=PromptStyle.DETAILED,
                template="Create a {subject} in {style} style. {requirements}",
                variables=["subject", "style", "requirements"],
            ),
            PromptTemplate(
                template_id="tpl_txt_creative",
                name="Creative Writing",
                domain=TaskDomain.TEXT_GENERATION,
                style=PromptStyle.CREATIVE,
                template="Write a {genre} piece about {topic}. {constraints}",
                variables=["genre", "topic", "constraints"],
            ),
            PromptTemplate(
                template_id="tpl_code_technical",
                name="Technical Code",
                domain=TaskDomain.CODE_GENERATION,
                style=PromptStyle.TECHNICAL,
                template="Write a {language} function that {description}. {requirements}",
                variables=["language", "description", "requirements"],
            ),
        ]

        for tpl in default_templates:
            self.templates[tpl.template_id] = tpl

    def get_template(self, template_id: str) -> Optional[PromptTemplate]:
        """获取模板"""
        return self.templates.get(template_id)

    def render_template(
        self,
        template_id: str,
        variables: Dict[str, str]
    ) -> Optional[str]:
        """渲染模板"""
        template = self.templates.get(template_id)
        if not template:
            return None

        rendered = template.template
        for var_name, var_value in variables.items():
            rendered = rendered.replace(f"{{{var_name}}}", var_value)

        return rendered


# 全局单例
_optimizer_instance: Optional[HybridPromptOptimizer] = None
_template_manager_instance: Optional[PromptTemplateManager] = None


def get_deep_prompt_optimizer() -> HybridPromptOptimizer:
    """获取深度提示词优化器"""
    global _optimizer_instance
    if _optimizer_instance is None:
        _optimizer_instance = HybridPromptOptimizer()
    return _optimizer_instance


def get_prompt_template_manager() -> PromptTemplateManager:
    """获取提示词模板管理器"""
    global _template_manager_instance
    if _template_manager_instance is None:
        _template_manager_instance = PromptTemplateManager()
    return _template_manager_instance
