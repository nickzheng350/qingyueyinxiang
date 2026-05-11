"""用户认证模块 - JWT认证和用户管理"""

import jwt
import hashlib
import time
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

logger = logging.getLogger("hydraflow.auth")


@dataclass
class User:
    """用户信息"""
    id: str
    username: str
    email: Optional[str] = None
    role: str = "user"
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    last_login: Optional[datetime] = None


class AuthManager:
    """认证管理器"""
    
    def __init__(self, secret_key: str = "hydraflow-secret-key"):
        self._secret_key = secret_key
        self._users: Dict[str, User] = {}
        self._token_store: Dict[str, Dict[str, Any]] = {}
        
        # 创建默认管理员用户
        self._create_default_admin()
    
    def _create_default_admin(self) -> None:
        """创建默认管理员用户"""
        admin_user = User(
            id="admin",
            username="admin",
            email="admin@hydraflow.local",
            role="admin",
            enabled=True
        )
        self._users["admin"] = admin_user
        logger.info("已创建默认管理员用户")
    
    def _hash_password(self, password: str, salt: Optional[str] = None) -> str:
        """哈希密码"""
        if salt is None:
            salt = hashlib.sha256(str(time.time()).encode()).hexdigest()[:16]
        return f"{salt}${hashlib.sha256((salt + password).encode()).hexdigest()}"
    
    def _verify_password(self, password: str, hashed: str) -> bool:
        """验证密码"""
        if "$" not in hashed:
            return False
        salt, hash_value = hashed.split("$", 1)
        computed_hash = hashlib.sha256((salt + password).encode()).hexdigest()
        return computed_hash == hash_value
    
    def create_user(
        self,
        username: str,
        password: str,
        email: Optional[str] = None,
        role: str = "user"
    ) -> Optional[User]:
        """创建用户"""
        if username in self._users:
            logger.warning(f"用户已存在: {username}")
            return None
        
        user = User(
            id=username,
            username=username,
            email=email,
            role=role,
            enabled=True
        )
        self._users[username] = user
        
        # 存储密码哈希（简单实现，实际应存储在数据库）
        self._token_store[f"user:{username}:password"] = self._hash_password(password)
        
        logger.info(f"创建用户: {username}")
        return user
    
    def authenticate(self, username: str, password: str) -> Optional[str]:
        """认证用户并生成JWT令牌"""
        user = self._users.get(username)
        if not user or not user.enabled:
            return None
        
        # 获取存储的密码哈希
        stored_hash = self._token_store.get(f"user:{username}:password")
        if not stored_hash:
            return None
        
        # 验证密码
        if not self._verify_password(password, stored_hash):
            logger.warning(f"认证失败: {username}")
            return None
        
        # 更新最后登录时间
        user.last_login = datetime.now()
        
        # 生成JWT令牌
        token = self._generate_token(username)
        self._token_store[f"token:{token}"] = {
            "username": username,
            "expires_at": datetime.now() + timedelta(hours=24)
        }
        
        logger.info(f"用户登录成功: {username}")
        return token
    
    def _generate_token(self, username: str) -> str:
        """生成JWT令牌"""
        payload = {
            "sub": username,
            "exp": datetime.now(tz=None) + timedelta(hours=24),
            "iat": datetime.now(tz=None),
            "iss": "hydraflow"
        }
        return jwt.encode(payload, self._secret_key, algorithm="HS256")
    
    def verify_token(self, token: str) -> Optional[str]:
        """验证JWT令牌"""
        try:
            # 禁用iat验证以避免时间同步问题
            payload = jwt.decode(
                token, 
                self._secret_key, 
                algorithms=["HS256"],
                options={"verify_iat": False}
            )
            username = payload.get("sub")
            
            # 检查本地存储（用于注销）
            stored = self._token_store.get(f"token:{token}")
            if not stored:
                return None
            
            # 检查过期
            if stored["expires_at"] < datetime.now():
                self._revoke_token(token)
                return None
            
            return username
        except jwt.ExpiredSignatureError:
            logger.warning("令牌已过期")
            self._revoke_token(token)
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"无效令牌: {e}")
            return None
    
    def _revoke_token(self, token: str) -> None:
        """吊销令牌"""
        if f"token:{token}" in self._token_store:
            del self._token_store[f"token:{token}"]
            logger.debug(f"令牌已吊销: {token[:20]}...")
    
    def logout(self, token: str) -> bool:
        """登出用户"""
        username = self.verify_token(token)
        if username:
            self._revoke_token(token)
            logger.info(f"用户登出: {username}")
            return True
        return False
    
    def get_user(self, username: str) -> Optional[User]:
        """获取用户信息"""
        return self._users.get(username)
    
    def update_user(
        self,
        username: str,
        **kwargs
    ) -> bool:
        """更新用户信息"""
        user = self._users.get(username)
        if not user:
            return False
        
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        logger.info(f"更新用户信息: {username}")
        return True
    
    def delete_user(self, username: str) -> bool:
        """删除用户"""
        if username == "admin":
            logger.warning("禁止删除管理员用户")
            return False
        
        if username in self._users:
            del self._users[username]
            # 清理相关数据
            keys_to_delete = [k for k in self._token_store.keys() if k.startswith(f"user:{username}:")]
            for key in keys_to_delete:
                del self._token_store[key]
            logger.info(f"删除用户: {username}")
            return True
        return False
    
    def list_users(self) -> list[User]:
        """列出所有用户"""
        return list(self._users.values())


# 全局单例
_auth_manager = None

def get_auth_manager() -> AuthManager:
    """获取认证管理器实例"""
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = AuthManager()
    return _auth_manager
