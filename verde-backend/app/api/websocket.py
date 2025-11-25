"""
WebSocket 실시간 통신
"""
from fastapi import WebSocket, WebSocketDisconnect
from typing import List, Dict, Set
import json
import logging
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    WebSocket 연결 관리자

    기능:
    - 클라이언트 연결 관리
    - 실시간 브로드캐스트
    - 채널별 구독 관리
    """

    def __init__(self):
        # 모든 활성 연결
        self.active_connections: List[WebSocket] = []

        # 채널별 구독자 관리
        self.subscriptions: Dict[str, Set[WebSocket]] = {
            "trending": set(),        # 실시간 검색어 순위
            "species_updates": set(), # 새로운 생물종 추가
            "stats": set(),           # 통계 업데이트
            "notifications": set()    # 일반 알림
        }

    async def connect(self, websocket: WebSocket, channels: List[str] = None):
        """
        새 클라이언트 연결

        Args:
            websocket: WebSocket 연결
            channels: 구독할 채널 리스트
        """
        await websocket.accept()
        self.active_connections.append(websocket)

        # 채널 구독
        if channels:
            for channel in channels:
                if channel in self.subscriptions:
                    self.subscriptions[channel].add(websocket)

        logger.info(f"WebSocket connected. Total: {len(self.active_connections)}")

        # 연결 환영 메시지
        await websocket.send_json({
            "type": "connected",
            "message": "Verde WebSocket에 연결되었습니다",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "channels": channels or []
        })

    def disconnect(self, websocket: WebSocket):
        """클라이언트 연결 종료"""
        # 활성 연결에서 제거
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

        # 모든 채널 구독 해제
        for channel, subscribers in self.subscriptions.items():
            if websocket in subscribers:
                subscribers.remove(websocket)

        logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")

    async def subscribe(self, websocket: WebSocket, channel: str):
        """채널 구독"""
        if channel in self.subscriptions:
            self.subscriptions[channel].add(websocket)
            await websocket.send_json({
                "type": "subscribed",
                "channel": channel,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })
            logger.info(f"Subscribed to channel: {channel}")
        else:
            await websocket.send_json({
                "type": "error",
                "message": f"Unknown channel: {channel}"
            })

    async def unsubscribe(self, websocket: WebSocket, channel: str):
        """채널 구독 해제"""
        if channel in self.subscriptions and websocket in self.subscriptions[channel]:
            self.subscriptions[channel].remove(websocket)
            await websocket.send_json({
                "type": "unsubscribed",
                "channel": channel,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })
            logger.info(f"Unsubscribed from channel: {channel}")

    async def broadcast(self, message: Dict):
        """
        모든 연결된 클라이언트에게 메시지 전송

        Args:
            message: 전송할 메시지 (dict)
        """
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Broadcast error: {str(e)}")
                disconnected.append(connection)

        # 끊어진 연결 정리
        for connection in disconnected:
            self.disconnect(connection)

    async def broadcast_to_channel(self, channel: str, message: Dict):
        """
        특정 채널 구독자에게만 메시지 전송

        Args:
            channel: 채널 이름
            message: 전송할 메시지
        """
        if channel not in self.subscriptions:
            logger.warning(f"Unknown channel: {channel}")
            return

        disconnected = []
        subscribers = self.subscriptions[channel]

        for connection in subscribers:
            try:
                await connection.send_json({
                    **message,
                    "channel": channel,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                })
            except Exception as e:
                logger.error(f"Channel broadcast error: {str(e)}")
                disconnected.append(connection)

        # 끊어진 연결 정리
        for connection in disconnected:
            self.disconnect(connection)

        logger.info(f"Broadcast to channel '{channel}': {len(subscribers)} subscribers")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """특정 클라이언트에게만 메시지 전송"""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Personal message error: {str(e)}")
            self.disconnect(websocket)

    def get_stats(self) -> Dict:
        """연결 통계"""
        return {
            "total_connections": len(self.active_connections),
            "subscriptions": {
                channel: len(subscribers)
                for channel, subscribers in self.subscriptions.items()
            }
        }


# 싱글톤 인스턴스
manager = ConnectionManager()


# =========================================================================
# WebSocket 이벤트 브로드캐스터
# =========================================================================
async def broadcast_trending_update(trending_data: List[Dict]):
    """
    실시간 검색어 순위 업데이트 브로드캐스트

    사용 예시:
    >>> from app.api.websocket import broadcast_trending_update
    >>> await broadcast_trending_update([
    ...     {"query": "호랑이", "score": 150.0},
    ...     {"query": "판다", "score": 120.0}
    ... ])
    """
    await manager.broadcast_to_channel("trending", {
        "type": "trending_update",
        "data": trending_data
    })


async def broadcast_species_added(species_data: Dict):
    """
    새로운 생물종 추가 알림

    사용 예시:
    >>> await broadcast_species_added({
    ...     "id": 123,
    ...     "name": "반달가슴곰",
    ...     "category": "동물"
    ... })
    """
    await manager.broadcast_to_channel("species_updates", {
        "type": "species_added",
        "data": species_data
    })


async def broadcast_stats_update(stats_data: Dict):
    """
    통계 업데이트 브로드캐스트

    사용 예시:
    >>> await broadcast_stats_update({
    ...     "total_species": 1234,
    ...     "endangered_count": 456
    ... })
    """
    await manager.broadcast_to_channel("stats", {
        "type": "stats_update",
        "data": stats_data
    })


async def broadcast_notification(notification: Dict):
    """
    일반 알림 브로드캐스트

    사용 예시:
    >>> await broadcast_notification({
    ...     "title": "시스템 공지",
    ...     "message": "데이터 업데이트가 완료되었습니다",
    ...     "level": "info"
    ... })
    """
    await manager.broadcast_to_channel("notifications", {
        "type": "notification",
        "data": notification
    })


# =========================================================================
# 백그라운드 작업 (주기적 업데이트)
# =========================================================================
async def periodic_trending_updates():
    """
    주기적으로 실시간 검색어 순위를 브로드캐스트

    30초마다 실행
    """
    while True:
        try:
            from app.cache import get_top_searches

            trending = get_top_searches(limit=10)
            if trending:
                await broadcast_trending_update(trending)

            await asyncio.sleep(30)  # 30초마다

        except Exception as e:
            logger.error(f"Periodic trending updates error: {str(e)}")
            await asyncio.sleep(30)
