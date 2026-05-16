"""数据库服务 - 支持多种数据库级别和配置"""

from typing import Optional, Dict, List, Any
from pathlib import Path
from datetime import datetime
from contextlib import asynccontextmanager

from src.core.config import get_settings, DatabaseTier


class DatabaseService:
    """统一数据库服务"""

    _instance: "DatabaseService | None" = None

    def __new__(cls) -> "DatabaseService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        self.settings = get_settings().database
        self._connection = None
        self._connect()

    def _connect(self):
        """根据配置连接数据库"""
        tier = self.settings.tier
        
        if tier == DatabaseTier.DEVELOPMENT:
            self._connect_sqlite()
        elif tier in [DatabaseTier.STANDARD, DatabaseTier.HIGH_AVAILABILITY]:
            self._connect_postgresql()
        elif tier == DatabaseTier.CLUSTER:
            self._connect_distributed()
        elif tier == DatabaseTier.ENTERPRISE:
            self._connect_enterprise()

    def _connect_sqlite(self):
        """连接SQLite数据库"""
        import sqlite3
        db_path = Path(self.settings.sqlite_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(str(db_path))
        self._init_tables()

    def _connect_postgresql(self):
        """连接PostgreSQL数据库"""
        try:
            import psycopg2
            self._connection = psycopg2.connect(
                host=self.settings.postgresql_host,
                port=self.settings.postgresql_port,
                database=self.settings.postgresql_db,
                user=self.settings.postgresql_user,
                password=self.settings.postgresql_password
            )
            self._init_tables()
        except ImportError:
            # 如果没有psycopg2，回退到SQLite
            self._connect_sqlite()

    def _connect_distributed(self):
        """连接分布式数据库（占位）"""
        self._connect_postgresql()

    def _connect_enterprise(self):
        """连接企业级数据库（占位）"""
        self._connect_postgresql()

    def _init_tables(self):
        """初始化数据库表"""
        if self._connection is None:
            return

        cursor = self._connection.cursor()
        
        # 创建文件元数据表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS file_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id TEXT UNIQUE NOT NULL,
                filename TEXT NOT NULL,
                size INTEGER,
                created_at TEXT,
                modified_at TEXT,
                metadata TEXT,
                user_id TEXT
            )
        ''')

        # 创建任务表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT UNIQUE NOT NULL,
                type TEXT NOT NULL,
                status TEXT NOT NULL,
                prompt TEXT,
                model_id TEXT,
                parameters TEXT,
                result TEXT,
                error TEXT,
                created_at TEXT,
                completed_at TEXT
            )
        ''')

        # 创建用户表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email TEXT,
                role TEXT DEFAULT 'user',
                enabled INTEGER DEFAULT 1,
                created_at TEXT,
                last_login TEXT
            )
        ''')

        # 创建技能表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                skill_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                type TEXT,
                version TEXT,
                enabled INTEGER DEFAULT 0,
                config TEXT,
                installed_at TEXT
            )
        ''')

        # 创建模型统计表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS model_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_id TEXT NOT NULL,
                usage_count INTEGER DEFAULT 0,
                total_tokens INTEGER DEFAULT 0,
                avg_latency REAL DEFAULT 0,
                last_used TEXT,
                FOREIGN KEY (model_id) REFERENCES models(model_id)
            )
        ''')

        # 创建模型配置表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS models (
                model_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT,
                function_type TEXT,
                source TEXT,
                config TEXT,
                enabled INTEGER DEFAULT 1,
                created_at TEXT
            )
        ''')

        self._connection.commit()
        cursor.close()

    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """执行查询并返回结果"""
        if self._connection is None:
            return []

        cursor = self._connection.cursor()
        cursor.execute(query, params)
        
        # 获取列名
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        results = []
        
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        
        cursor.close()
        return results

    def execute_update(self, query: str, params: tuple = ()) -> int:
        """执行更新操作并返回影响的行数"""
        if self._connection is None:
            return 0

        cursor = self._connection.cursor()
        cursor.execute(query, params)
        self._connection.commit()
        affected = cursor.rowcount
        cursor.close()
        return affected

    def get_tier_info(self) -> dict:
        """获取当前数据库级别信息"""
        tier = self.settings.tier
        features = self._get_tier_features(tier)
        
        return {
            'tier': tier.value,
            'tier_label': self._get_tier_label(tier),
            'features': features,
            'replication_enabled': self.settings.replication_enabled,
            'read_replicas': self.settings.read_replicas,
            'backup_enabled': self.settings.backup_enabled,
            'backup_schedule': self.settings.backup_schedule,
            'encryption_enabled': self.settings.encryption_enabled,
            'high_availability': tier in [DatabaseTier.HIGH_AVAILABILITY, DatabaseTier.CLUSTER, DatabaseTier.ENTERPRISE],
            'cluster_mode': tier in [DatabaseTier.CLUSTER, DatabaseTier.ENTERPRISE],
            'multi_datacenter': tier == DatabaseTier.ENTERPRISE,
            'score': self.settings.database_capacity_score
        }

    def _get_tier_features(self, tier: DatabaseTier) -> List[str]:
        """获取数据库级别的特性列表"""
        features_map = {
            DatabaseTier.DEVELOPMENT: [
                'SQLite本地数据库',
                '单节点部署',
                '适合开发测试'
            ],
            DatabaseTier.STANDARD: [
                'PostgreSQL单节点',
                '基础性能优化',
                '适合小型生产环境'
            ],
            DatabaseTier.HIGH_AVAILABILITY: [
                '主从复制架构',
                '自动故障转移',
                '读写分离',
                '高可用性保障'
            ],
            DatabaseTier.CLUSTER: [
                '分布式架构',
                '数据分片',
                '水平扩展',
                '多节点负载均衡'
            ],
            DatabaseTier.ENTERPRISE: [
                '多数据中心部署',
                '跨区域灾备',
                '自动故障转移',
                '企业级安全审计',
                '高级监控告警'
            ]
        }
        return features_map.get(tier, [])

    def _get_tier_label(self, tier: DatabaseTier) -> str:
        """获取数据库级别中文标签"""
        labels = {
            DatabaseTier.DEVELOPMENT: '开发环境',
            DatabaseTier.STANDARD: '标准',
            DatabaseTier.HIGH_AVAILABILITY: '高可用',
            DatabaseTier.CLUSTER: '集群',
            DatabaseTier.ENTERPRISE: '企业级'
        }
        return labels.get(tier, tier.value)

    def get_connection_status(self) -> dict:
        """获取数据库连接状态"""
        try:
            if self._connection is None:
                return {'connected': False, 'error': '未连接'}
            
            # 测试连接
            cursor = self._connection.cursor()
            cursor.execute('SELECT 1')
            cursor.fetchone()
            cursor.close()
            
            return {
                'connected': True,
                'tier': self.settings.tier.value,
                'backend': 'SQLite' if self.settings.tier == DatabaseTier.DEVELOPMENT else 'PostgreSQL'
            }
        except Exception as e:
            return {'connected': False, 'error': str(e)}

    def get_database_stats(self) -> dict:
        """获取数据库统计信息"""
        stats = {
            'tables': [],
            'total_records': 0
        }
        
        try:
            tables = self.execute_query("""
                SELECT name FROM sqlite_master WHERE type='table'
            """)
            
            for table in tables:
                table_name = table['name']
                count = self.execute_query(f"SELECT COUNT(*) as count FROM {table_name}")
                stats['tables'].append({
                    'name': table_name,
                    'record_count': count[0]['count'] if count else 0
                })
                stats['total_records'] += count[0]['count'] if count else 0
        except Exception:
            pass
        
        return stats

    def backup_database(self, backup_path: Optional[str] = None) -> bool:
        """备份数据库"""
        if self._connection is None:
            return False

        try:
            if backup_path is None:
                backup_path = f"./data/backup/db_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            
            backup_path = Path(backup_path)
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            
            if self.settings.tier == DatabaseTier.DEVELOPMENT:
                # SQLite备份
                import shutil
                db_path = Path(self.settings.sqlite_path)
                shutil.copy(str(db_path), str(backup_path))
            else:
                # PostgreSQL备份（占位）
                pass
            
            return True
        except Exception as e:
            print(f"备份失败: {e}")
            return False

    def restore_database(self, backup_path: str) -> bool:
        """恢复数据库"""
        if self._connection is None:
            return False

        try:
            if self.settings.tier == DatabaseTier.DEVELOPMENT:
                import shutil
                db_path = Path(self.settings.sqlite_path)
                shutil.copy(backup_path, str(db_path))
                self._connect()  # 重新连接
            else:
                # PostgreSQL恢复（占位）
                pass
            
            return True
        except Exception as e:
            print(f"恢复失败: {e}")
            return False

    def close(self):
        """关闭数据库连接"""
        if self._connection:
            self._connection.close()
            self._connection = None


def get_database_service() -> DatabaseService:
    """获取数据库服务单例"""
    return DatabaseService()
