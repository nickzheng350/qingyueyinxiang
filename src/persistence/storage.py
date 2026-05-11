"""数据持久化框架 - SQLite后端"""

import sqlite3
import json
from datetime import datetime
from typing import Any, Dict, Optional, List, Tuple
import logging
import os

logger = logging.getLogger("hydraflow.persistence")


class SQLiteStorage:
    """SQLite 持久化存储"""
    
    def __init__(self, db_path: str = "data/hydraflow.db"):
        self._db_path = db_path
        self._ensure_db_directory()
        self._init_tables()
    
    def _ensure_db_directory(self) -> None:
        """确保数据库目录存在"""
        dir_path = os.path.dirname(self._db_path)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
    
    def _init_tables(self) -> None:
        """初始化数据库表"""
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.cursor()
            
            # 任务表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    prompt TEXT NOT NULL,
                    parameters TEXT NOT NULL,
                    model_id TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    progress REAL DEFAULT 0.0,
                    result TEXT,
                    error TEXT,
                    created_at TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT,
                    metadata TEXT
                )
            """)
            
            # 任务索引
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_tasks_type ON tasks(type)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_tasks_created ON tasks(created_at)
            """)
            
            # 模型使用统计
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS model_stats (
                    model_id TEXT PRIMARY KEY,
                    total_calls INTEGER DEFAULT 0,
                    success_calls INTEGER DEFAULT 0,
                    fail_calls INTEGER DEFAULT 0,
                    total_duration REAL DEFAULT 0.0,
                    last_call_at TEXT,
                    avg_latency REAL DEFAULT 0.0
                )
            """)
            
            # 技能表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS skills (
                    skill_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    version TEXT DEFAULT '1.0.0',
                    description TEXT,
                    type TEXT NOT NULL DEFAULT 'local',
                    path TEXT NOT NULL,
                    config TEXT,
                    enabled BOOLEAN DEFAULT 1,
                    installed_at TEXT NOT NULL,
                    last_used_at TEXT
                )
            """)
            
            # 配置表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS config (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            conn.commit()
            logger.debug("数据库表初始化完成")
    
    def _serialize(self, data: Any) -> str:
        """序列化数据"""
        return json.dumps(data)
    
    def _deserialize(self, data: str) -> Any:
        """反序列化数据"""
        if not data:
            return None
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return data
    
    def _now(self) -> str:
        """获取当前时间字符串"""
        return datetime.now().isoformat()
    
    # === 任务操作 ===
    
    def save_task(self, task_data: Dict[str, Any]) -> None:
        """保存任务"""
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO tasks (
                    id, type, prompt, parameters, model_id, status,
                    progress, result, error, created_at, started_at,
                    completed_at, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task_data["id"],
                task_data["type"],
                task_data["prompt"],
                self._serialize(task_data["parameters"]),
                task_data["model_id"],
                task_data.get("status", "pending"),
                task_data.get("progress", 0.0),
                self._serialize(task_data.get("result")),
                task_data.get("error"),
                task_data.get("created_at", self._now()),
                task_data.get("started_at"),
                task_data.get("completed_at"),
                self._serialize(task_data.get("metadata", {})),
            ))
            conn.commit()
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务"""
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_task(row)
    
    def _row_to_task(self, row: Tuple) -> Dict[str, Any]:
        """将数据库行转换为任务字典"""
        return {
            "id": row[0],
            "type": row[1],
            "prompt": row[2],
            "parameters": self._deserialize(row[3]),
            "model_id": row[4],
            "status": row[5],
            "progress": row[6],
            "result": self._deserialize(row[7]),
            "error": row[8],
            "created_at": row[9],
            "started_at": row[10],
            "completed_at": row[11],
            "metadata": self._deserialize(row[12]),
        }
    
    def list_tasks(
        self,
        status: Optional[str] = None,
        task_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """列出任务"""
        query = "SELECT * FROM tasks"
        params = []
        
        conditions = []
        if status:
            conditions.append("status = ?")
            params.append(status)
        if task_type:
            conditions.append("type = ?")
            params.append(task_type)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [self._row_to_task(row) for row in rows]
    
    def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def get_task_count(self, status: Optional[str] = None) -> int:
        """获取任务数量"""
        query = "SELECT COUNT(*) FROM tasks"
        params = []
        
        if status:
            query += " WHERE status = ?"
            params.append(status)
        
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            row = cursor.fetchone()
            return row[0] if row else 0
    
    # === 模型统计 ===
    
    def update_model_stats(self, model_id: str, success: bool, duration: float) -> None:
        """更新模型统计"""
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT total_calls, success_calls, fail_calls, total_duration
                FROM model_stats WHERE model_id = ?
            """, (model_id,))
            row = cursor.fetchone()
            
            if row:
                total_calls = row[0] + 1
                success_calls = row[1] + (1 if success else 0)
                fail_calls = row[2] + (0 if success else 1)
                total_duration = row[3] + duration
                avg_latency = total_duration / total_calls
                
                cursor.execute("""
                    UPDATE model_stats SET
                        total_calls = ?, success_calls = ?, fail_calls = ?,
                        total_duration = ?, avg_latency = ?, last_call_at = ?
                    WHERE model_id = ?
                """, (total_calls, success_calls, fail_calls, total_duration, avg_latency, self._now(), model_id))
            else:
                cursor.execute("""
                    INSERT INTO model_stats (
                        model_id, total_calls, success_calls, fail_calls,
                        total_duration, avg_latency, last_call_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (model_id, 1, 1 if success else 0, 0 if success else 1, duration, duration, self._now()))
            
            conn.commit()
    
    def get_model_stats(self, model_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取模型统计"""
        query = "SELECT * FROM model_stats"
        params = []
        
        if model_id:
            query += " WHERE model_id = ?"
            params.append(model_id)
        
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [{
                "model_id": row[0],
                "total_calls": row[1],
                "success_calls": row[2],
                "fail_calls": row[3],
                "total_duration": row[4],
                "last_call_at": row[5],
                "avg_latency": row[6],
                "success_rate": row[2] / row[1] if row[1] > 0 else 0.0,
            } for row in rows]
    
    # === 技能操作 ===
    
    def save_skill(self, skill_data: Dict[str, Any]) -> None:
        """保存技能"""
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO skills (
                    skill_id, name, version, description, type, path,
                    config, enabled, installed_at, last_used_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                skill_data["skill_id"],
                skill_data["name"],
                skill_data.get("version", "1.0.0"),
                skill_data.get("description"),
                skill_data.get("type", "local"),
                skill_data["path"],
                self._serialize(skill_data.get("config", {})),
                skill_data.get("enabled", True),
                skill_data.get("installed_at", self._now()),
                skill_data.get("last_used_at"),
            ))
            conn.commit()
    
    def get_skill(self, skill_id: str) -> Optional[Dict[str, Any]]:
        """获取技能"""
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM skills WHERE skill_id = ?", (skill_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return {
                "skill_id": row[0],
                "name": row[1],
                "version": row[2],
                "description": row[3],
                "type": row[4],
                "path": row[5],
                "config": self._deserialize(row[6]),
                "enabled": bool(row[7]),
                "installed_at": row[8],
                "last_used_at": row[9],
            }
    
    def list_skills(self, skill_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """列出技能"""
        query = "SELECT * FROM skills"
        params = []
        
        if skill_type:
            query += " WHERE type = ?"
            params.append(skill_type)
        
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [{
                "skill_id": row[0],
                "name": row[1],
                "version": row[2],
                "description": row[3],
                "type": row[4],
                "path": row[5],
                "config": self._deserialize(row[6]),
                "enabled": bool(row[7]),
                "installed_at": row[8],
                "last_used_at": row[9],
            } for row in rows]
    
    def delete_skill(self, skill_id: str) -> bool:
        """删除技能"""
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM skills WHERE skill_id = ?", (skill_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    # === 配置操作 ===
    
    def set_config(self, key: str, value: Any) -> None:
        """设置配置"""
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO config (key, value, updated_at)
                VALUES (?, ?, ?)
            """, (key, self._serialize(value), self._now()))
            conn.commit()
    
    def get_config(self, key: str) -> Optional[Any]:
        """获取配置"""
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM config WHERE key = ?", (key,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._deserialize(row[0])


# 全局单例
_storage = None

def get_storage() -> SQLiteStorage:
    """获取存储实例"""
    global _storage
    if _storage is None:
        _storage = SQLiteStorage()
    return _storage
