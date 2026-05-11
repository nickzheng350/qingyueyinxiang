"""WebSocket 路由 - 实时通信端点"""

import asyncio
import json
import logging
from typing import Dict, Any

from fastapi import WebSocket, WebSocketDisconnect
from fastapi.routing import APIRoute

logger = logging.getLogger("hydraflow.ws.routes")


class WebSocketRoutes:
    """WebSocket 路由集合"""
    
    def __init__(self, ws_manager):
        self._ws_manager = ws_manager
    
    async def task_status_ws(self, websocket: WebSocket, task_id: str):
        """任务状态实时推送 WebSocket"""
        queue = await self._ws_manager.connect()
        
        try:
            await websocket.accept()
            
            # 订阅任务
            await self._ws_manager.subscribe_to_task(task_id, queue)
            
            # 发送初始消息
            await websocket.send_json({
                "type": "connected",
                "message": f"已连接到任务 {task_id}",
                "task_id": task_id
            })
            
            # 持续接收消息
            while True:
                try:
                    # 接收客户端消息（带超时）
                    msg = await asyncio.wait_for(queue.get(), timeout=30.0)
                    await websocket.send_text(msg)
                except asyncio.TimeoutError:
                    # 发送心跳
                    await websocket.send_json({
                        "type": "ping",
                        "timestamp": asyncio.get_event_loop().time()
                    })
                except WebSocketDisconnect:
                    break
                except Exception as e:
                    logger.error(f"WebSocket 错误: {e}")
                    break
        
        finally:
            await self._ws_manager.disconnect(queue)
            logger.debug(f"任务 {task_id} 的 WebSocket 连接已关闭")
    
    async def broadcast_ws(self, websocket: WebSocket):
        """广播消息 WebSocket"""
        queue = await self._ws_manager.connect()
        
        try:
            await websocket.accept()
            
            await websocket.send_json({
                "type": "connected",
                "message": "已连接到广播频道"
            })
            
            while True:
                try:
                    msg = await asyncio.wait_for(queue.get(), timeout=30.0)
                    await websocket.send_text(msg)
                except asyncio.TimeoutError:
                    await websocket.send_json({
                        "type": "ping",
                        "timestamp": asyncio.get_event_loop().time()
                    })
                except WebSocketDisconnect:
                    break
                except Exception as e:
                    logger.error(f"广播 WebSocket 错误: {e}")
                    break
        
        finally:
            await self._ws_manager.disconnect(queue)
            logger.debug("广播 WebSocket 连接已关闭")
    
    def register_routes(self, app):
        """注册 WebSocket 路由到应用"""
        app.add_api_websocket_route(
            "/ws/tasks/{task_id}",
            self.task_status_ws,
            name="task_status_ws"
        )
        
        app.add_api_websocket_route(
            "/ws/broadcast",
            self.broadcast_ws,
            name="broadcast_ws"
        )
