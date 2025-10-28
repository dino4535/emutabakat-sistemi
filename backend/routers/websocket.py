"""
WebSocket Router
Real-time bildirimler için WebSocket endpoint
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from backend.websocket.manager import websocket_manager
from backend.auth import get_current_user_from_token
from backend.models import User
import json


router = APIRouter(prefix="/ws", tags=["WebSocket"])


@router.websocket("/notifications")
async def websocket_endpoint(websocket: WebSocket, token: str = None):
    """
    WebSocket endpoint for real-time notifications
    
    Usage (Frontend):
        const ws = new WebSocket(`ws://localhost:8000/ws/notifications?token=${token}`);
        
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log('Received:', data);
        };
    """
    # Token doğrulama
    if not token:
        await websocket.close(code=1008, reason="Token required")
        return
    
    try:
        # Token'dan user al
        from backend.database import get_db
        db = next(get_db())
        user = get_current_user_from_token(token, db)
        
        if not user:
            await websocket.close(code=1008, reason="Invalid token")
            return
        
        # Connection oluştur
        await websocket_manager.connect(websocket, user.id, user.company_id)
        
        try:
            # Welcome message
            await websocket.send_json({
                "type": "connected",
                "message": f"Hoş geldiniz, {user.full_name}!",
                "user_id": user.id
            })
            
            # Connection açık tut (heartbeat)
            while True:
                # Client'tan mesaj bekle (ping-pong için)
                data = await websocket.receive_text()
                
                # Ping-pong
                if data == "ping":
                    await websocket.send_json({"type": "pong"})
                
        except WebSocketDisconnect:
            websocket_manager.disconnect(websocket, user.id, user.company_id)
            
    except Exception as e:
        print(f"WebSocket error: {e}")
        try:
            await websocket.close(code=1011, reason=str(e))
        except:
            pass


@router.get("/stats")
async def get_websocket_stats():
    """WebSocket istatistikleri (admin)"""
    return {
        "active_users": websocket_manager.get_active_users(),
        "connection_count": websocket_manager.get_connection_count(),
        "company_rooms": len(websocket_manager.company_rooms)
    }

