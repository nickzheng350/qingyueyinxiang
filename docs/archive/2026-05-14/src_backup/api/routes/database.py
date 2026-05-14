"""数据库管理API路由"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional

from src.services.database_service import get_database_service, DatabaseService

router = APIRouter(prefix="/database", tags=["数据库管理"])


@router.get("/info", summary="获取数据库信息")
async def get_database_info(db: DatabaseService = Depends(get_database_service)):
    """
    获取当前数据库配置和级别信息
    """
    try:
        return {
            "success": True,
            "tier_info": db.get_tier_info(),
            "connection_status": db.get_connection_status()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取数据库信息失败: {str(e)}")


@router.get("/status", summary="获取数据库连接状态")
async def get_database_status(db: DatabaseService = Depends(get_database_service)):
    """
    获取数据库连接状态
    """
    status = db.get_connection_status()
    return {
        "success": status['connected'],
        **status
    }


@router.get("/stats", summary="获取数据库统计信息")
async def get_database_stats(db: DatabaseService = Depends(get_database_service)):
    """
    获取数据库表和记录统计信息
    """
    try:
        stats = db.get_database_stats()
        return {
            "success": True,
            **stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取数据库统计失败: {str(e)}")


@router.post("/backup", summary="备份数据库")
async def backup_database(
    backup_path: Optional[str] = None,
    db: DatabaseService = Depends(get_database_service)
):
    """
    备份数据库
    
    - **backup_path**: 备份文件路径（可选）
    """
    try:
        success = db.backup_database(backup_path)
        if success:
            return {"success": True, "message": "数据库备份成功"}
        else:
            return {"success": False, "message": "数据库备份失败"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据库备份失败: {str(e)}")


@router.post("/restore", summary="恢复数据库")
async def restore_database(
    backup_path: str,
    db: DatabaseService = Depends(get_database_service)
):
    """
    从备份恢复数据库
    
    - **backup_path**: 备份文件路径
    """
    try:
        success = db.restore_database(backup_path)
        if success:
            return {"success": True, "message": "数据库恢复成功"}
        else:
            return {"success": False, "message": "数据库恢复失败"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据库恢复失败: {str(e)}")


@router.get("/tier-features", summary="获取数据库级别特性")
async def get_tier_features(db: DatabaseService = Depends(get_database_service)):
    """
    获取当前数据库级别的所有特性
    """
    tier_info = db.get_tier_info()
    return {
        "success": True,
        "tier": tier_info['tier'],
        "tier_label": tier_info['tier_label'],
        "features": tier_info['features'],
        "score": tier_info['score']
    }


@router.get("/tier-options", summary="获取所有数据库级别选项")
async def get_tier_options():
    """
    获取所有可用的数据库级别选项
    """
    from src.core.config import DatabaseTier
    
    tiers = []
    for tier in DatabaseTier:
        tiers.append({
            "value": tier.value,
            "label": {
                DatabaseTier.DEVELOPMENT: '开发环境',
                DatabaseTier.STANDARD: '标准',
                DatabaseTier.HIGH_AVAILABILITY: '高可用',
                DatabaseTier.CLUSTER: '集群',
                DatabaseTier.ENTERPRISE: '企业级'
            }.get(tier, tier.value)
        })
    
    return {
        "success": True,
        "tiers": tiers
    }
