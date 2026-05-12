"""
插件管理 API - 提供管理员添加和管理模块的接口
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
import os
import json
from pathlib import Path

from src.plugins.manager import PluginManager
from src.api.security import get_current_admin_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/plugins", tags=["plugins"])

# 全局插件管理器实例
plugin_manager = PluginManager()


class PluginInfo(BaseModel):
    """插件信息模型"""
    name: str
    version: str
    description: str
    author: str
    priority: int
    enabled: bool
    dependencies: List[str] = []


class PluginConfigUpdate(BaseModel):
    """插件配置更新模型"""
    config: Dict[str, Any]


class PluginInstallRequest(BaseModel):
    """插件安装请求模型"""
    name: str
    version: Optional[str] = None
    config: Optional[Dict[str, Any]] = None


@router.on_event("startup")
async def startup_event():
    """启动时自动加载插件"""
    plugin_manager.discover_plugins()
    plugin_manager.load_all_plugins()
    logger.info("插件系统初始化完成")


@router.get("/", response_model=List[PluginInfo])
async def list_plugins(
    current_user: dict = Depends(get_current_admin_user)
):
    """
    列出所有插件
    需要管理员权限
    """
    plugins = []

    # 获取所有已注册的插件
    all_plugin_classes = plugin_manager.get_all_plugins()
    for name, cls in all_plugin_classes.items():
        inst = cls()
        loaded = name in plugin_manager.get_all_loaded_plugins()
        plugins.append(PluginInfo(
            name=inst.get_name(),
            version=inst.get_version(),
            description=inst.get_description(),
            author=inst.get_author(),
            priority=inst.get_priority(),
            enabled=loaded,
            dependencies=inst.get_dependencies()
        ))

    return plugins


@router.get("/loaded", response_model=List[PluginInfo])
async def list_loaded_plugins(
    current_user: dict = Depends(get_current_admin_user)
):
    """
    列出所有已加载的插件
    需要管理员权限
    """
    loaded = plugin_manager.get_all_loaded_plugins()
    plugins = []
    for name, inst in loaded.items():
        plugins.append(PluginInfo(
            name=inst.get_name(),
            version=inst.get_version(),
            description=inst.get_description(),
            author=inst.get_author(),
            priority=inst.get_priority(),
            enabled=True,
            dependencies=inst.get_dependencies()
        ))
    return plugins


@router.post("/load/{plugin_name}")
async def load_plugin(
    plugin_name: str,
    config: Optional[PluginConfigUpdate] = None,
    current_user: dict = Depends(get_current_admin_user)
):
    """
    加载指定插件
    需要管理员权限
    """
    plugin_inst = plugin_manager.load_plugin(
        plugin_name,
        config.config if config else None
    )

    if not plugin_inst:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"插件加载失败: {plugin_name}"
        )

    return {
        "status": "success",
        "message": f"插件 {plugin_name} 加载成功",
        "plugin": {
            "name": plugin_inst.get_name(),
            "version": plugin_inst.get_version()
        }
    }


@router.post("/unload/{plugin_name}")
async def unload_plugin(
    plugin_name: str,
    current_user: dict = Depends(get_current_admin_user)
):
    """
    卸载插件
    需要管理员权限
    """
    success = plugin_manager.unload_plugin(plugin_name)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"插件未找到或卸载失败: {plugin_name}"
        )

    return {
        "status": "success",
        "message": f"插件 {plugin_name} 卸载成功"
    }


@router.get("/{plugin_name}/config")
async def get_plugin_config(
    plugin_name: str,
    current_user: dict = Depends(get_current_admin_user)
):
    """
    获取插件配置
    需要管理员权限
    """
    plugin_inst = plugin_manager.get_plugin(plugin_name)
    if not plugin_inst:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"插件未加载: {plugin_name}"
        )

    config = plugin_inst.get_config()
    return {
        "status": "success",
        "config": config.dict() if config else None
    }


@router.put("/{plugin_name}/config")
async def update_plugin_config(
    plugin_name: str,
    config_update: PluginConfigUpdate,
    current_user: dict = Depends(get_current_admin_user)
):
    """
    更新插件配置
    需要管理员权限
    """
    plugin_inst = plugin_manager.get_plugin(plugin_name)
    if not plugin_inst:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"插件未加载: {plugin_name}"
        )

    # 重新加载插件以应用新配置
    plugin_manager.unload_plugin(plugin_name)
    plugin_inst = plugin_manager.load_plugin(plugin_name, config_update.config)

    return {
        "status": "success",
        "message": f"插件配置已更新: {plugin_name}"
    }


@router.post("/install")
async def install_plugin(
    request: PluginInstallRequest,
    current_user: dict = Depends(get_current_admin_user)
):
    """
    安装插件（从本地目录）
    需要管理员权限
    """
    # 这里可以扩展为从远程仓库安装
    return {
        "status": "info",
        "message": "请使用 /install/upload 上传插件包",
        "supported_methods": ["upload", "git", "pip"]
    }


@router.post("/install/upload")
async def upload_and_install_plugin(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_admin_user)
):
    """
    上传并安装插件
    需要管理员权限
    """
    import tempfile
    import zipfile

    # 创建临时目录
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # 保存上传的文件
        file_path = temp_path / file.filename
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # 解压插件
        if file.filename.endswith('.zip'):
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                extract_path = temp_path / "extracted"
                zip_ref.extractall(extract_path)

                # 查找插件目录
                plugin_dir = None
                for item in extract_path.iterdir():
                    if item.is_dir() and (item / '__init__.py').exists():
                        plugin_dir = item
                        break

                if plugin_dir:
                    # 移动到 plugins 目录
                    target_dir = Path("plugins") / plugin_dir.name
                    if not target_dir.exists():
                        import shutil
                        shutil.copytree(plugin_dir, target_dir)

                        # 发现并加载插件
                        plugin_manager.discover_plugins()

                        return {
                            "status": "success",
                            "message": f"插件已安装: {plugin_dir.name}",
                            "plugin_dir": str(target_dir)
                        }

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的插件包格式"
        )


@router.get("/{plugin_name}/endpoints")
async def get_plugin_endpoints(
    plugin_name: str,
    current_user: dict = Depends(get_current_admin_user)
):
    """
    获取插件提供的 API 端点
    需要管理员权限
    """
    plugin_inst = plugin_manager.get_plugin(plugin_name)
    if not plugin_inst:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"插件未加载: {plugin_name}"
        )

    endpoints = plugin_inst.get_endpoints()
    return {
        "status": "success",
        "plugin": plugin_name,
        "endpoints": endpoints
    }


@router.get("/{plugin_name}/commands")
async def get_plugin_commands(
    plugin_name: str,
    current_user: dict = Depends(get_current_admin_user)
):
    """
    获取插件提供的 CLI 命令
    需要管理员权限
    """
    plugin_inst = plugin_manager.get_plugin(plugin_name)
    if not plugin_inst:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"插件未加载: {plugin_name}"
        )

    commands = plugin_inst.get_commands()
    return {
        "status": "success",
        "plugin": plugin_name,
        "commands": commands
    }
