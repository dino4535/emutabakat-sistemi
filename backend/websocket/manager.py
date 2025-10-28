"""
WebSocket Connection Manager
Real-time bildirimler için
"""
from fastapi import WebSocket
from typing import Dict, List
import json


class ConnectionManager:
    """WebSocket connection manager"""
    
    def __init__(self):
        # User ID -> WebSocket connections mapping
        self.active_connections: Dict[int, List[WebSocket]] = {}
        # Company ID -> WebSocket connections mapping (room-based)
        self.company_rooms: Dict[int, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int, company_id: int):
        """Yeni connection ekle"""
        await websocket.accept()
        
        # User connections
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        
        # Company room
        if company_id not in self.company_rooms:
            self.company_rooms[company_id] = []
        self.company_rooms[company_id].append(websocket)
        
        print(f"✅ WebSocket connected: User {user_id}, Company {company_id}")
    
    def disconnect(self, websocket: WebSocket, user_id: int, company_id: int):
        """Connection kaldır"""
        # User connections
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        
        # Company room
        if company_id in self.company_rooms:
            if websocket in self.company_rooms[company_id]:
                self.company_rooms[company_id].remove(websocket)
            if not self.company_rooms[company_id]:
                del self.company_rooms[company_id]
        
        print(f"❌ WebSocket disconnected: User {user_id}, Company {company_id}")
    
    async def send_personal_message(self, message: dict, user_id: int):
        """Belirli bir kullanıcıya mesaj gönder"""
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    print(f"Error sending message to user {user_id}: {e}")
    
    async def broadcast_to_company(self, message: dict, company_id: int):
        """Şirket geneline broadcast"""
        if company_id in self.company_rooms:
            for connection in self.company_rooms[company_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    print(f"Error broadcasting to company {company_id}: {e}")
    
    async def broadcast_all(self, message: dict):
        """Tüm kullanıcılara broadcast"""
        for connections in self.active_connections.values():
            for connection in connections:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    print(f"Error broadcasting: {e}")
    
    def get_active_users(self) -> List[int]:
        """Aktif kullanıcı ID'leri"""
        return list(self.active_connections.keys())
    
    def get_connection_count(self) -> int:
        """Toplam connection sayısı"""
        return sum(len(connections) for connections in self.active_connections.values())


# Global manager instance
websocket_manager = ConnectionManager()

