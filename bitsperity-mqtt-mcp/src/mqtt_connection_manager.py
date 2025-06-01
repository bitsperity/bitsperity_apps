"""
bitsperity-mqtt-mcp - MQTT Connection Manager
Phase 2: Real MQTT Integration mit aiomqtt

Verwaltet MQTT Connections mit sicherer Session-basierter Verwaltung
"""

import uuid
import asyncio
import logging
from typing import Dict, Optional, Any, List, Set
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from urllib.parse import urlparse
import json

# Phase 2: aiomqtt import für real MQTT integration
import aiomqtt

logger = logging.getLogger(__name__)


class MQTTSession:
    """
    Einzelne MQTT Session mit Real MQTT Client
    
    Phase 2: Enhanced mit aiomqtt real connection
    """
    
    def __init__(self, session_id: str, connection_string: str, cipher_suite: Fernet):
        self.session_id = session_id
        self.created_at = datetime.now()
        self.last_accessed = datetime.now()
        self.cipher_suite = cipher_suite
        
        # Parse connection string
        self.parsed_connection = self._parse_connection_string(connection_string)
        
        # Session state
        self.is_connected = False
        self.connection_error: Optional[str] = None
        
        # Phase 2: Real MQTT client
        self.mqtt_client: Optional[aiomqtt.Client] = None
        self._client_task: Optional[asyncio.Task] = None
        
        # Phase 2: Topic und message tracking für collection tools
        self.subscribed_topics: Set[str] = set()
        self.topic_messages: Dict[str, List[Dict[str, Any]]] = {}
        
        # Encrypted credentials (nie im Klartext speichern)
        self.encrypted_credentials = self._encrypt_credentials(
            self.parsed_connection.get('username'),
            self.parsed_connection.get('password')
        )
    
    def _parse_connection_string(self, connection_string: str) -> Dict[str, Any]:
        """
        Parse MQTT Connection String
        
        Format: mqtt://[username:password@]broker:port[/client_id]
        """
        try:
            parsed = urlparse(connection_string)
            
            if parsed.scheme != 'mqtt':
                raise ValueError("Connection string must start with 'mqtt://'")
            
            return {
                'broker': parsed.hostname or 'localhost',
                'port': parsed.port or 1883,
                'username': parsed.username,
                'password': parsed.password,
                'client_id': parsed.path.lstrip('/') if parsed.path else None
            }
        except Exception as e:
            raise ValueError(f"Invalid connection string: {e}")
    
    def _encrypt_credentials(self, username: Optional[str], password: Optional[str]) -> Dict[str, Optional[bytes]]:
        """Encrypt username and password"""
        encrypted = {}
        
        if username:
            encrypted['username'] = self.cipher_suite.encrypt(username.encode())
        else:
            encrypted['username'] = None
            
        if password:
            encrypted['password'] = self.cipher_suite.encrypt(password.encode())
        else:
            encrypted['password'] = None
            
        return encrypted
    
    def get_credentials(self) -> Dict[str, Optional[str]]:
        """Decrypt and return credentials"""
        credentials = {}
        
        if self.encrypted_credentials['username']:
            credentials['username'] = self.cipher_suite.decrypt(
                self.encrypted_credentials['username']
            ).decode()
        else:
            credentials['username'] = None
            
        if self.encrypted_credentials['password']:
            credentials['password'] = self.cipher_suite.decrypt(
                self.encrypted_credentials['password']
            ).decode()
        else:
            credentials['password'] = None
            
        return credentials
    
    def update_last_accessed(self):
        """Update last accessed timestamp"""
        self.last_accessed = datetime.now()
    
    def is_expired(self, ttl_hours: int = 1) -> bool:
        """Check if session is expired (default: 1 hour TTL)"""
        expiry_time = self.created_at + timedelta(hours=ttl_hours)
        return datetime.now() > expiry_time
    
    async def disconnect(self):
        """Phase 2: Properly disconnect MQTT client"""
        try:
            if self._client_task and not self._client_task.done():
                self._client_task.cancel()
                try:
                    await self._client_task
                except asyncio.CancelledError:
                    pass
            
            # aiomqtt clients are handled by context managers
            # No need to explicitly disconnect, just clear the reference
            self.mqtt_client = None
            
            self.is_connected = False
            logger.debug(f"Session {self.session_id} disconnected properly")
            
        except Exception as e:
            logger.error(f"Error disconnecting session {self.session_id}: {e}")
            self.is_connected = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dict (without credentials)"""
        return {
            'session_id': self.session_id,
            'broker': self.parsed_connection['broker'],
            'port': self.parsed_connection['port'],
            'client_id': self.parsed_connection.get('client_id'),
            'created_at': self.created_at.isoformat(),
            'last_accessed': self.last_accessed.isoformat(),
            'is_connected': self.is_connected,
            'connection_error': self.connection_error,
            'subscribed_topics': list(self.subscribed_topics)
        }


class MQTTConnectionManager:
    """
    MQTT Connection Manager
    
    Phase 2 Features:
    - Real aiomqtt client integration
    - Session-based connection management
    - Credential encryption mit Fernet
    - Automatic session cleanup
    - Max 5 concurrent connections
    """
    
    def __init__(self, max_connections: int = 5):
        self.max_connections = max_connections
        self.sessions: Dict[str, MQTTSession] = {}
        
        # Generate encryption key (in production: from environment)
        self.cipher_suite = Fernet(Fernet.generate_key())
        
        # Background cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None
        
        logger.info(f"MQTTConnectionManager initialized (max_connections={max_connections})")
    
    def _start_cleanup_task(self):
        """Start background task für session cleanup"""
        try:
            # Only start if there's a running loop
            loop = asyncio.get_running_loop()
            if self._cleanup_task is None or self._cleanup_task.done():
                self._cleanup_task = loop.create_task(self._cleanup_expired_sessions())
        except RuntimeError:
            # No running event loop, skip background task
            # This happens during testing when objects are created outside async context
            logger.debug("No running event loop, skipping background cleanup task")
    
    async def _cleanup_expired_sessions(self):
        """Background task: Cleanup expired sessions every 10 minutes"""
        while True:
            try:
                await asyncio.sleep(600)  # 10 minutes
                
                expired_sessions = [
                    session_id for session_id, session in self.sessions.items()
                    if session.is_expired()
                ]
                
                for session_id in expired_sessions:
                    await self.close_session(session_id)
                    logger.info(f"Cleaned up expired session: {session_id}")
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Session cleanup error: {e}")
    
    async def establish_connection(self, connection_string: str) -> Dict[str, Any]:
        """
        Establish new MQTT connection
        
        Args:
            connection_string: mqtt://[username:password@]broker:port[/client_id]
            
        Returns:
            Session information dict
        """
        try:
            # Start cleanup task if not running
            self._start_cleanup_task()
            
            # Check connection limit
            if len(self.sessions) >= self.max_connections:
                raise Exception(f"Maximum connections reached ({self.max_connections})")
            
            # Create new session
            session_id = str(uuid.uuid4())
            session = MQTTSession(session_id, connection_string, self.cipher_suite)
            
            # Phase 2: Real MQTT connection
            await self._establish_real_mqtt_connection(session)
            
            # Store session only if connection successful
            if session.is_connected:
                self.sessions[session_id] = session
                logger.info(f"Established MQTT connection: {session_id}")
            else:
                # Cleanup failed connection
                await session.disconnect()
                raise Exception(session.connection_error or "Connection failed")
            
            return {
                'session_id': session_id,
                'broker': session.parsed_connection['broker'],
                'port': session.parsed_connection['port'],
                'status': 'connected' if session.is_connected else 'failed',
                'created_at': session.created_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to establish connection: {e}")
            raise Exception(f"Connection failed: {str(e)}")
    
    async def _establish_real_mqtt_connection(self, session: MQTTSession):
        """
        Phase 2: Real MQTT connection mit aiomqtt
        Replace mock implementation
        """
        try:
            # Get decrypted credentials
            credentials = session.get_credentials()
            
            # Create aiomqtt client
            client_id = session.parsed_connection.get('client_id') or f"bitsperity-mqtt-mcp-{session.session_id[:8]}"
            
            # Configure client options
            client_options = {
                'hostname': session.parsed_connection['broker'],
                'port': session.parsed_connection['port'],
                'identifier': client_id,
                'timeout': 30.0,  # 30 second timeout
                'keepalive': 60,  # 60 second keepalive
            }
            
            # Add authentication if provided
            if credentials['username'] and credentials['password']:
                client_options['username'] = credentials['username']
                client_options['password'] = credentials['password']
                logger.debug(f"Using authentication for {session.parsed_connection['broker']}")
            
            # Create client (but don't connect yet - will be done by context manager)
            session.mqtt_client = aiomqtt.Client(**client_options)
            
            logger.info(f"Connecting to MQTT broker: {session.parsed_connection['broker']}:{session.parsed_connection['port']}")
            
            # Test connection by trying to enter context manager
            try:
                # Try to connect temporarily to verify credentials and connectivity
                async with session.mqtt_client:
                    # Connection successful if we get here
                    session.is_connected = True
                    session.connection_error = None
                    logger.info(f"Successfully connected to {session.parsed_connection['broker']} as {client_id}")
                    
                # After exiting context manager, we need to recreate the client for actual use
                # because aiomqtt clients are not reusable after context exit
                session.mqtt_client = aiomqtt.Client(**client_options)
                    
            except aiomqtt.MqttError as e:
                session.is_connected = False
                session.connection_error = f"MQTT Error: {str(e)}"
                logger.error(f"MQTT connection failed: {e}")
                
        except asyncio.TimeoutError:
            session.is_connected = False
            session.connection_error = f"Connection timeout to {session.parsed_connection['broker']}:{session.parsed_connection['port']}"
            logger.error(session.connection_error)
            
        except Exception as e:
            session.is_connected = False
            session.connection_error = f"Connection failed: {str(e)}"
            logger.error(f"MQTT connection error: {e}")
    
    def list_active_connections(self) -> Dict[str, Any]:
        """
        List all active MQTT connections
        
        Returns:
            Dict with connection information
        """
        active_sessions = []
        
        for session in self.sessions.values():
            session.update_last_accessed()
            active_sessions.append(session.to_dict())
        
        logger.debug(f"Listed {len(active_sessions)} active connections")
        
        return {
            'active_connections': active_sessions,
            'total_count': len(active_sessions),
            'max_connections': self.max_connections,
            'timestamp': datetime.now().isoformat()
        }
    
    async def close_session(self, session_id: str) -> Dict[str, Any]:
        """
        Close MQTT session
        
        Args:
            session_id: Session ID to close
            
        Returns:
            Closure confirmation dict
        """
        try:
            if session_id not in self.sessions:
                raise Exception(f"Session not found: {session_id}")
            
            session = self.sessions[session_id]
            
            # Phase 2: Real MQTT disconnect
            await session.disconnect()
            
            # Remove session
            del self.sessions[session_id]
            
            logger.info(f"Closed MQTT session: {session_id}")
            
            return {
                'session_id': session_id,
                'status': 'closed',
                'closed_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to close session {session_id}: {e}")
            raise Exception(f"Session closure failed: {str(e)}")
    
    async def get_session(self, session_id: str) -> Optional[MQTTSession]:
        """
        Get session by ID
        
        Args:
            session_id: Session ID
            
        Returns:
            MQTTSession or None if not found
        """
        session = self.sessions.get(session_id)
        
        if session:
            session.update_last_accessed()
            
            # Check if expired
            if session.is_expired():
                await self.close_session(session_id)
                return None
            
            # Phase 2: Check if MQTT client is still connected
            if session.mqtt_client and not session.is_connected:
                # Connection lost, mark as disconnected
                session.is_connected = False
                session.connection_error = "Connection lost"
                logger.warning(f"Session {session_id} connection lost")
        
        return session
    
    async def cleanup_all_sessions(self):
        """Close all active sessions (for shutdown)"""
        session_ids = list(self.sessions.keys())
        
        for session_id in session_ids:
            try:
                await self.close_session(session_id)
            except Exception as e:
                logger.error(f"Error closing session {session_id}: {e}")
        
        # Cancel cleanup task
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
        
        logger.info("All MQTT sessions cleaned up") 