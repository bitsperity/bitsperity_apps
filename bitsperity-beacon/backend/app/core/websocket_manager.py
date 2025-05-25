"""
WebSocket Manager für Real-time Updates
"""
import asyncio
import json
from typing import List, Dict, Any
from fastapi import WebSocket, WebSocketDisconnect
import structlog

logger = structlog.get_logger(__name__)


class WebSocketManager:
    """WebSocket Manager für Real-time Updates"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_info: Dict[WebSocket, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str = None) -> None:
        """Neue WebSocket Verbindung akzeptieren"""
        try:
            await websocket.accept()
            self.active_connections.append(websocket)
            
            # Speichere Connection Info
            self.connection_info[websocket] = {
                "client_id": client_id or f"client_{len(self.active_connections)}",
                "connected_at": asyncio.get_event_loop().time()
            }
            
            logger.info("WebSocket Verbindung hergestellt",
                       client_id=self.connection_info[websocket]["client_id"],
                       total_connections=len(self.active_connections))
            
            # Sende Welcome Message
            await self.send_personal_message({
                "type": "connection_established",
                "message": "Verbindung zu Bitsperity Beacon hergestellt",
                "client_id": self.connection_info[websocket]["client_id"]
            }, websocket)
            
        except Exception as e:
            logger.error("Fehler bei WebSocket Verbindung", error=str(e))
            await self.disconnect(websocket)
    
    async def disconnect(self, websocket: WebSocket) -> None:
        """WebSocket Verbindung schließen"""
        try:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
            
            client_info = self.connection_info.pop(websocket, {})
            client_id = client_info.get("client_id", "unknown")
            
            logger.info("WebSocket Verbindung geschlossen",
                       client_id=client_id,
                       total_connections=len(self.active_connections))
            
        except Exception as e:
            logger.error("Fehler beim Schließen der WebSocket Verbindung", error=str(e))
    
    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket) -> None:
        """Sende Nachricht an spezifische WebSocket Verbindung"""
        try:
            await websocket.send_text(json.dumps(message))
            
        except WebSocketDisconnect:
            await self.disconnect(websocket)
        except Exception as e:
            logger.error("Fehler beim Senden der persönlichen Nachricht", error=str(e))
            await self.disconnect(websocket)
    
    async def broadcast(self, message: Dict[str, Any]) -> None:
        """Sende Nachricht an alle verbundenen Clients"""
        if not self.active_connections:
            return
        
        # Erstelle JSON Message
        json_message = json.dumps(message)
        
        # Sende an alle Verbindungen
        disconnected_connections = []
        
        for connection in self.active_connections:
            try:
                await connection.send_text(json_message)
                
            except WebSocketDisconnect:
                disconnected_connections.append(connection)
            except Exception as e:
                logger.error("Fehler beim Broadcast", error=str(e))
                disconnected_connections.append(connection)
        
        # Entferne disconnected connections
        for connection in disconnected_connections:
            await self.disconnect(connection)
        
        logger.debug("Broadcast gesendet",
                    message_type=message.get("type", "unknown"),
                    recipients=len(self.active_connections))
    
    async def broadcast_service_registered(self, service_data: Dict[str, Any]) -> None:
        """Broadcast Service Registration Event"""
        await self.broadcast({
            "type": "service_registered",
            "event": "service_registered",
            "data": service_data,
            "timestamp": asyncio.get_event_loop().time()
        })
    
    async def broadcast_service_deregistered(self, service_id: str, service_name: str = None) -> None:
        """Broadcast Service Deregistration Event"""
        await self.broadcast({
            "type": "service_deregistered",
            "event": "service_deregistered",
            "data": {
                "service_id": service_id,
                "service_name": service_name
            },
            "timestamp": asyncio.get_event_loop().time()
        })
    
    async def broadcast_service_updated(self, service_data: Dict[str, Any]) -> None:
        """Broadcast Service Update Event"""
        await self.broadcast({
            "type": "service_updated",
            "event": "service_updated",
            "data": service_data,
            "timestamp": asyncio.get_event_loop().time()
        })
    
    async def broadcast_service_heartbeat(self, service_id: str, expires_at: str) -> None:
        """Broadcast Service Heartbeat Event"""
        await self.broadcast({
            "type": "service_heartbeat",
            "event": "service_heartbeat",
            "data": {
                "service_id": service_id,
                "expires_at": expires_at
            },
            "timestamp": asyncio.get_event_loop().time()
        })
    
    async def broadcast_services_cleanup(self, removed_count: int) -> None:
        """Broadcast Services Cleanup Event"""
        if removed_count > 0:
            await self.broadcast({
                "type": "services_cleanup",
                "event": "services_cleanup",
                "data": {
                    "removed_count": removed_count
                },
                "timestamp": asyncio.get_event_loop().time()
            })
    
    def get_connection_count(self) -> int:
        """Hole Anzahl aktiver Verbindungen"""
        return len(self.active_connections)
    
    def get_connection_info(self) -> List[Dict[str, Any]]:
        """Hole Info über alle Verbindungen"""
        return [
            {
                "client_id": info["client_id"],
                "connected_at": info["connected_at"]
            }
            for info in self.connection_info.values()
        ] 