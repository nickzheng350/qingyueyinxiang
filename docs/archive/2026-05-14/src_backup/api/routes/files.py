"""文件管理API路由"""

from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from fastapi.responses import FileResponse, StreamingResponse
from typing import List, Optional

from src.services.storage_service import get_storage_service, StorageService
from src.core.config import get_settings

router = APIRouter(prefix="/files", tags=["文件管理"])


@router.post("/upload", summary="上传文件")
async def upload_file(
    file: UploadFile = File(...),
    destination: Optional[str] = "",
    storage: StorageService = Depends(get_storage_service)
):
    """
    上传文件到存储系统
    
    - **file**: 要上传的文件
    - **destination**: 目标目录（可选）
    """
    # 检查文件大小
    settings = get_settings().storage
    file_size_mb = file.size / (1024 * 1024) if file.size else 0
    
    if file_size_mb > settings.max_file_size_mb:
        raise HTTPException(
            status_code=400,
            detail=f"文件大小超过限制 ({file_size_mb:.2f}MB > {settings.max_file_size_mb}MB)"
        )
    
    # 检查文件扩展名
    ext = file.filename.split('.')[-1].lower() if '.' in file.filename else ''
    if settings.denied_extensions and ext in [e[1:].lower() for e in settings.denied_extensions]:
        raise HTTPException(status_code=400, detail=f"不允许上传 {ext} 类型文件")
    
    try:
        file_id = storage.upload_file(file.file, file.filename, destination)
        file_info = storage.get_file_info(file_id)
        
        return {
            "success": True,
            "file_id": file_id,
            "filename": file.filename,
            "size": file_info['size'] if file_info else 0,
            "message": "文件上传成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")


@router.get("/download/{file_id}", summary="下载文件")
async def download_file(
    file_id: str,
    storage: StorageService = Depends(get_storage_service)
):
    """
    根据文件ID下载文件
    
    - **file_id**: 文件标识
    """
    if not storage.exists(file_id):
        raise HTTPException(status_code=404, detail="文件不存在")
    
    try:
        file, filename = storage.download_file(file_id)
        return StreamingResponse(file, media_type="application/octet-stream", headers={
            "Content-Disposition": f"attachment; filename={filename}"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件下载失败: {str(e)}")


@router.get("/list", summary="列出文件")
async def list_files(
    prefix: Optional[str] = "",
    storage: StorageService = Depends(get_storage_service)
):
    """
    列出存储中的文件
    
    - **prefix**: 目录前缀（可选）
    """
    try:
        files = storage.list_files(prefix)
        return {
            "success": True,
            "files": files,
            "count": len(files)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件列表获取失败: {str(e)}")


@router.get("/info/{file_id}", summary="获取文件信息")
async def get_file_info(
    file_id: str,
    storage: StorageService = Depends(get_storage_service)
):
    """
    获取文件详细信息
    
    - **file_id**: 文件标识
    """
    file_info = storage.get_file_info(file_id)
    if not file_info:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    return {
        "success": True,
        "file": file_info
    }


@router.delete("/{file_id}", summary="删除文件")
async def delete_file(
    file_id: str,
    storage: StorageService = Depends(get_storage_service)
):
    """
    删除指定文件
    
    - **file_id**: 文件标识
    """
    if not storage.exists(file_id):
        raise HTTPException(status_code=404, detail="文件不存在")
    
    try:
        success = storage.delete_file(file_id)
        return {
            "success": success,
            "message": "文件删除成功" if success else "文件删除失败"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件删除失败: {str(e)}")


@router.get("/storage-info", summary="获取存储信息")
async def get_storage_info(
    storage: StorageService = Depends(get_storage_service)
):
    """
    获取存储系统信息和使用情况
    """
    settings = get_settings().storage
    
    return {
        "success": True,
        "tier": settings.tier.value,
        "backend": settings.backend.value,
        "features": storage.get_tier_features(),
        "tier_score": storage.get_tier_score(),
        "usage": storage.get_storage_usage(),
        "max_file_size_mb": settings.max_file_size_mb,
        "backup_enabled": settings.backup_enabled,
        "encryption_enabled": settings.encryption_enabled,
        "compression_enabled": settings.compression_enabled,
        "versioning_enabled": settings.versioning_enabled,
        "cdn_enabled": settings.cdn_enabled
    }


@router.post("/upload-multiple", summary="批量上传文件")
async def upload_multiple_files(
    files: List[UploadFile] = File(...),
    destination: Optional[str] = "",
    storage: StorageService = Depends(get_storage_service)
):
    """
    批量上传多个文件
    
    - **files**: 要上传的文件列表
    - **destination**: 目标目录（可选）
    """
    results = []
    settings = get_settings().storage
    
    for file in files:
        try:
            # 检查文件大小
            file_size_mb = file.size / (1024 * 1024) if file.size else 0
            
            if file_size_mb > settings.max_file_size_mb:
                results.append({
                    "filename": file.filename,
                    "success": False,
                    "error": f"文件大小超过限制 ({file_size_mb:.2f}MB > {settings.max_file_size_mb}MB)"
                })
                continue
            
            file_id = storage.upload_file(file.file, file.filename, destination)
            file_info = storage.get_file_info(file_id)
            
            results.append({
                "filename": file.filename,
                "success": True,
                "file_id": file_id,
                "size": file_info['size'] if file_info else 0
            })
        except Exception as e:
            results.append({
                "filename": file.filename,
                "success": False,
                "error": str(e)
            })
    
    success_count = sum(1 for r in results if r['success'])
    
    return {
        "success": success_count == len(files),
        "total_files": len(files),
        "success_count": success_count,
        "failed_count": len(files) - success_count,
        "results": results
    }
