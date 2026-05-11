"""技能管理器 - 安装、搜索、管理技能"""

import json
import shutil
import zipfile
import logging
from pathlib import Path
from typing import Any

from src.core.config import get_config
from src.core.exceptions import SkillNotFoundError

logger = logging.getLogger("hydraflow.skills")


class SkillManager:
    _instance: "SkillManager | None" = None

    def __new__(cls) -> "SkillManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        config = get_config()
        self._skills_dir = config.project_root / "skills"
        self._market_cache_dir = config.project_root / ".market_cache"
        self._skills: dict[str, dict[str, Any]] = {}
        self._load_skills()

    def _load_skills(self) -> None:
        if not self._skills_dir.exists():
            return
        for skill_dir in self._skills_dir.iterdir():
            if skill_dir.is_dir():
                manifest = skill_dir / "manifest.json"
                if manifest.exists():
                    try:
                        with open(manifest, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        data["type"] = data.get("type", "local")
                        data["path"] = str(skill_dir)
                        self._skills[data.get("skill_id", skill_dir.name)] = data
                    except (json.JSONDecodeError, OSError) as e:
                        logger.error(f"加载技能失败 {skill_dir}: {e}")

    def list_skills(self) -> list[dict[str, Any]]:
        return list(self._skills.values())

    def list_skills_by_type(self, skill_type: str) -> list[dict[str, Any]]:
        return [s for s in self._skills.values() if s.get("type") == skill_type]

    def get_skill(self, skill_id: str) -> dict[str, Any]:
        if skill_id not in self._skills:
            raise SkillNotFoundError(skill_id)
        return self._skills[skill_id]

    def install_skill_from_path(self, path: str, skill_type: str = "local") -> dict[str, Any]:
        source = Path(path)
        if not source.exists():
            return {"status": "error", "message": f"路径不存在: {path}"}
        if source.is_file() and source.suffix == ".zip":
            return self._install_from_zip(source, skill_type)
        if source.is_dir():
            return self._install_from_directory(source, skill_type)
        return {"status": "error", "message": f"不支持的路径类型: {path}"}

    def _install_from_zip(self, zip_path: Path, skill_type: str) -> dict[str, Any]:
        target_dir = self._skills_dir / skill_type
        target_dir.mkdir(parents=True, exist_ok=True)
        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                skill_name = zip_path.stem
                extract_dir = target_dir / skill_name
                zf.extractall(extract_dir)
                manifest = extract_dir / "manifest.json"
                if manifest.exists():
                    with open(manifest, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    skill_id = data.get("skill_id", skill_name)
                    data["type"] = skill_type
                    data["path"] = str(extract_dir)
                    self._skills[skill_id] = data
                    return {
                        "status": "success",
                        "message": f"技能安装成功: {data.get('name', skill_id)}",
                        "skill_id": skill_id,
                        "name": data.get("name", skill_id),
                        "path": str(extract_dir),
                    }
                return {"status": "error", "message": "ZIP 中缺少 manifest.json"}
        except (zipfile.BadZipFile, OSError) as e:
            return {"status": "error", "message": f"解压失败: {e}"}

    def _install_from_directory(self, source_dir: Path, skill_type: str) -> dict[str, Any]:
        manifest = source_dir / "manifest.json"
        if not manifest.exists():
            return {"status": "error", "message": "目录中缺少 manifest.json"}
        target_dir = self._skills_dir / skill_type
        target_dir.mkdir(parents=True, exist_ok=True)
        try:
            with open(manifest, "r", encoding="utf-8") as f:
                data = json.load(f)
            skill_id = data.get("skill_id", source_dir.name)
            dest = target_dir / skill_id
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(source_dir, dest)
            data["type"] = skill_type
            data["path"] = str(dest)
            self._skills[skill_id] = data
            return {
                "status": "success",
                "message": f"技能安装成功: {data.get('name', skill_id)}",
                "skill_id": skill_id,
                "name": data.get("name", skill_id),
                "path": str(dest),
            }
        except (json.JSONDecodeError, OSError) as e:
            return {"status": "error", "message": f"安装失败: {e}"}

    def install_skill_from_market(self, skill_id: str) -> dict[str, Any]:
        return {
            "status": "error",
            "message": f"市场安装功能暂未实现 (skill_id: {skill_id})。请使用 install_skill_from_path 从本地安装。",
        }

    def uninstall_skill(self, skill_id: str) -> dict[str, Any]:
        if skill_id not in self._skills:
            raise SkillNotFoundError(skill_id)
        skill = self._skills[skill_id]
        skill_path = skill.get("path")
        if skill_path:
            path = Path(skill_path)
            if path.exists():
                shutil.rmtree(path)
        del self._skills[skill_id]
        return {"status": "success", "message": f"技能已卸载: {skill_id}"}

    def search_market_skills(
        self, query: str = "", category: str = "", limit: int = 10
    ) -> list[dict[str, Any]]:
        return []

    def get_market_categories(self) -> dict[str, Any]:
        config = get_config()
        return config.categories_config

    def get_featured_skills(self, limit: int = 5) -> list[dict[str, Any]]:
        return []

    def get_statistics(self) -> dict[str, Any]:
        by_type: dict[str, int] = {}
        for skill in self._skills.values():
            t = skill.get("type", "unknown")
            by_type[t] = by_type.get(t, 0) + 1
        return {
            "total_skills": len(self._skills),
            "by_type": by_type,
        }
    
    def execute_skill(self, skill_id: str, **kwargs) -> dict[str, Any]:
        """执行技能"""
        from src.skills.skill_engine import get_skill_engine
        
        if skill_id not in self._skills:
            return {
                "status": "error",
                "message": f"技能未找到：{skill_id}",
            }
        
        skill = self._skills[skill_id]
        engine = get_skill_engine()
        
        # 如果技能未注册到引擎，先注册
        if skill_id not in engine.list_skills():
            self._register_skill_to_engine(engine, skill)
        
        # 执行技能
        result = engine.execute_skill_sync(skill_id, **kwargs)
        
        return {
            "status": "success" if result.success else "error",
            "skill_id": skill_id,
            "data": result.data,
            "error": result.error,
            "execution_time": result.execution_time,
            "metadata": result.metadata,
        }
    
    def _register_skill_to_engine(self, engine, skill: dict) -> None:
        """将技能注册到引擎"""
        skill_id = skill.get("skill_id")
        skill_name = skill.get("name", skill_id)
        skill_version = skill.get("version", "1.0.0")
        skill_path = skill.get("path")
        skill_config = skill.get("config", {})
        
        if not skill_path:
            logger.warning(f"技能 {skill_id} 缺少路径信息，无法注册到引擎")
            return
        
        # 查找执行器入口
        skill_dir = Path(skill_path)
        
        # 优先查找 executor.py
        executor_py = skill_dir / "executor.py"
        if executor_py.exists():
            engine.register_skill(
                skill_id=skill_id,
                skill_name=skill_name,
                skill_version=skill_version,
                executor_type="dynamic",
                module_path=str(executor_py),
                config=skill_config,
            )
            logger.info(f"技能 {skill_id} 已注册到引擎（动态执行器）")
            return
        
        # 查找 config.yaml 或 config.json
        config_yaml = skill_dir / "config.yaml"
        config_yml = skill_dir / "config.yml"
        config_json = skill_dir / "config.json"
        
        if config_yaml.exists():
            engine.register_skill(
                skill_id=skill_id,
                skill_name=skill_name,
                skill_version=skill_version,
                executor_type="config_based",
                config_path=str(config_yaml),
                config=skill_config,
            )
            logger.info(f"技能 {skill_id} 已注册到引擎（配置执行器）")
            return
        elif config_yml.exists():
            engine.register_skill(
                skill_id=skill_id,
                skill_name=skill_name,
                skill_version=skill_version,
                executor_type="config_based",
                config_path=str(config_yml),
                config=skill_config,
            )
            logger.info(f"技能 {skill_id} 已注册到引擎（配置执行器）")
            return
        elif config_json.exists():
            engine.register_skill(
                skill_id=skill_id,
                skill_name=skill_name,
                skill_version=skill_version,
                executor_type="config_based",
                config_path=str(config_json),
                config=skill_config,
            )
            logger.info(f"技能 {skill_id} 已注册到引擎（配置执行器）")
            return
        
        logger.warning(f"技能 {skill_id} 未找到执行器入口，跳过注册")
