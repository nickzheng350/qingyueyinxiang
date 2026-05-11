"""WebSocket 管理器 - 实时推送任务状态"""

import asyncio
import json
import logging
from typing import Dict, Set, Optional, Any, Callable
from datetime import datetime

logger = logging.getLogger("hydraflow.websocket")


class WebSocketManager:
    """WebSocket 连接管理器"""
    
    def __init__(self):
        self._active_connections: Set[asyncio.Queue] = set()
        self._task_subscriptions: Dict[str, Set[asyncio.Queue]] = {}
        self._lock = asyncio.Lock()
    
    async def connect(self) -> asyncio.Queue:
        """建立新连接"""
        queue = asyncio.Queue(maxsize=100)
        async with self._lock:
            self._active_connections.add(queue)
        logger.debug(f"WebSocket 连接建立，当前连接数: {len(self._active_connections)}")
        return queue
    
    async def disconnect(self, queue: asyncio.Queue) -> None:
        """断开连接"""
        async with self._lock:
            self._active_connections.discard(queue)
            
            # 移除所有订阅
            for task_id in list(self._task_subscriptions.keys()):
                if queue in self._task_subscriptions[task_id]:
                    self._task_subscriptions[task_id].discard(queue)
                    if not self._task_subscriptions[task_id]:
                        del self._task_subscriptions[task_id]
        
        logger.debug(f"WebSocket 连接断开，当前连接数: {len(self._active_connections)}")
    
    async def subscribe_to_task(self, task_id: str, queue: asyncio.Queue) -> None:
        """订阅任务状态"""
        async with self._lock:
            if task_id not in self._task_subscriptions:
                self._task_subscriptions[task_id] = set()
            self._task_subscriptions[task_id].add(queue)
        
        logger.debug(f"订阅任务: {task_id}")
    
    async def unsubscribe_from_task(self, task_id: str, queue: asyncio.Queue) -> None:
        """取消订阅任务"""
        async with self._lock:
            if task_id in self._task_subscriptions:
                self._task_subscriptions[task_id].discard(queue)
                if not self._task_subscriptions[task_id]:
                    del self._task_subscriptions[task_id]
        
        logger.debug(f"取消订阅任务: {task_id}")
    
    async def broadcast(self, message: Dict[str, Any]) -> None:
        """广播消息到所有连接"""
        message_str = json.dumps(message, ensure_ascii=False)
        
        disconnected = []
        async with self._lock:
            for queue in self._active_connections:
                try:
                    queue.put_nowait(message_str)
                except asyncio.QueueFull:
                    disconnected.append(queue)
                except Exception as e:
                    logger.error(f"广播失败: {e}")
                    disconnected.append(queue)
            
            # 移除断开的连接
            for queue in disconnected:
                self._active_connections.discard(queue)
    
    async def send_to_task_subscribers(self, task_id: str, message: Dict[str, Any]) -> None:
        """发送消息到任务订阅者"""
        message_str = json.dumps(message, ensure_ascii=False)
        
        disconnected = []
        async with self._lock:
            if task_id not in self._task_subscriptions:
                return
            
            for queue in self._task_subscriptions[task_id]:
                try:
                    queue.put_nowait(message_str)
                except asyncio.QueueFull:
                    disconnected.append(queue)
                except Exception as e:
                    logger.error(f"发送到任务订阅者失败: {e}")
                    disconnected.append(queue)
            
            # 移除断开的连接
            for queue in disconnected:
                self._task_subscriptions[task_id].discard(queue)
            
            if not self._task_subscriptions[task_id]:
                del self._task_subscriptions[task_id]
        
        logger.debug(f"发送消息到任务 {task_id} 的订阅者")
    
    async def send_task_update(self, task_id: str, status: str, progress: float, **kwargs) -> None:
        """发送任务更新"""
        message = {
            "type": "task_update",
            "task_id": task_id,
            "status": status,
            "progress": progress,
            "timestamp": datetime.now().isoformat(),
            **kwargs
        }
        
        await self.send_to_task_subscribers(task_id, message)
    
    def get_connection_count(self) -> int:
        """获取当前连接数"""
        return len(self._active_connections)
    
    def get_subscription_count(self, task_id: Optional[str] = None) -> int:
        """获取订阅数"""
        if task_id:
            return len(self._task_subscriptions.get(task_id, set()))
        return sum(len(subscribers) for subscribers in self._task_subscriptions.values())


# 全局单例
_ws_manager = None

def get_ws_manager() -> WebSocketManager:
    """获取 WebSocket 管理器实例"""
    global _ws_manager
    if _ws_manager is None:
        _ws_manager = WebSocketManager()
    return _ws_manager
