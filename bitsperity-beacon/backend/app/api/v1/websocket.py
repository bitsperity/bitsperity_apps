"""
WebSocket API Endpoints
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends
import structlog

from app.core.websocket_manager import WebSocketManager

logger = structlog.get_logger(__name__)

# Global WebSocket Manager - wird von main.py gesetzt
websocket_manager: WebSocketManager = None

def set_websocket_manager(ws_manager: WebSocketManager):
    """Setze WebSocket Manager"""
    global websocket_manager
    websocket_manager = ws_manager

def get_websocket_manager() -> WebSocketManager:
    """Dependency für WebSocket Manager"""
    if websocket_manager is None:
        raise RuntimeError("WebSocket Manager nicht initialisiert")
    return websocket_manager

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: str = Query(None, description="Optional client ID")
):
    """WebSocket Endpoint für Real-time Updates"""
    ws_manager = get_websocket_manager()
    
    await ws_manager.connect(websocket, client_id)
    
    try:
        while True:
            # Warte auf Nachrichten vom Client
            data = await websocket.receive_text()
            
            # Hier könnten Client-Nachrichten verarbeitet werden
            # Für jetzt nur Echo
            await ws_manager.send_personal_message({
                "type": "echo",
                "message": f"Echo: {data}"
            }, websocket)
            
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error("WebSocket Fehler", error=str(e))
        await ws_manager.disconnect(websocket) 