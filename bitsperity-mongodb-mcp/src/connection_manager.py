import asyncio
import hashlib
import logging
import time
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse
import pymongo
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ConfigurationError, ServerSelectionTimeoutError
from cryptography.fernet import Fernet
import os

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manages dynamic MongoDB connections with security and session management."""
    
    def __init__(self, session_ttl: int = 3600, max_connections: int = 10):
        self.session_ttl = session_ttl
        self.max_connections = max_connections
        self.connections: Dict[str, Dict[str, Any]] = {}
        self.cipher_suite = Fernet(Fernet.generate_key())
        self._cleanup_task = None
        self._start_cleanup_task()
        
    def _start_cleanup_task(self):
        """Start the cleanup task for expired connections."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_expired_connections())
    
    async def _cleanup_expired_connections(self):
        """Periodically cleanup expired connections."""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                await self.cleanup_expired_sessions()
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
    
    def _generate_session_id(self, connection_string: str) -> str:
        """Generate a unique session ID for a connection."""
        # Use a hash of the connection string + timestamp for uniqueness
        timestamp = str(int(time.time()))
        data = f"{connection_string}_{timestamp}".encode()
        return hashlib.sha256(data).hexdigest()[:16]
    
    def _encrypt_connection_string(self, connection_string: str) -> bytes:
        """Encrypt connection string for secure storage in memory."""
        return self.cipher_suite.encrypt(connection_string.encode())
    
    def _decrypt_connection_string(self, encrypted_data: bytes) -> str:
        """Decrypt connection string."""
        return self.cipher_suite.decrypt(encrypted_data).decode()
    
    def _parse_connection_string(self, connection_string: str) -> Dict[str, Any]:
        """Parse and validate MongoDB connection string."""
        try:
            parsed = urlparse(connection_string)
            if parsed.scheme not in ['mongodb', 'mongodb+srv']:
                raise ValueError(f"Invalid scheme: {parsed.scheme}")
            
            return {
                'scheme': parsed.scheme,
                'hostname': parsed.hostname,
                'port': parsed.port,
                'database': parsed.path.lstrip('/') if parsed.path else None,
                'username': parsed.username,
                'has_auth': bool(parsed.username and parsed.password)
            }
        except Exception as e:
            raise ValueError(f"Invalid connection string format: {e}")
    
    async def establish_connection(self, connection_string: str) -> str:
        """
        Establish a new MongoDB connection and return session ID.
        
        Args:
            connection_string: MongoDB connection string
            
        Returns:
            session_id: Unique identifier for this connection session
            
        Raises:
            ValueError: If connection string is invalid
            ConnectionError: If unable to connect to MongoDB
        """
        # Check connection limit
        if len(self.connections) >= self.max_connections:
            await self.cleanup_expired_sessions()
            if len(self.connections) >= self.max_connections:
                raise ConnectionError(f"Maximum connections ({self.max_connections}) reached")
        
        # Parse and validate connection string
        parsed_info = self._parse_connection_string(connection_string)
        
        # Test connection
        try:
            client = MongoClient(
                connection_string,
                serverSelectionTimeoutMS=5000,  # 5 second timeout
                connectTimeoutMS=5000,
                maxPoolSize=10,
                retryWrites=True
            )
            
            # Test connection with a simple command
            client.admin.command('ping')
            server_info = client.server_info()
            
            # Generate session ID
            session_id = self._generate_session_id(connection_string)
            
            # Store connection info
            self.connections[session_id] = {
                'client': client,
                'connection_string': self._encrypt_connection_string(connection_string),
                'created_at': time.time(),
                'last_used': time.time(),
                'server_info': server_info,
                'parsed_info': parsed_info,
                'database_names': None  # Will be cached on first request
            }
            
            logger.info(f"Connection established: {session_id} -> {parsed_info['hostname']}")
            return session_id
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            raise ConnectionError(f"Failed to connect to MongoDB: {e}")
        except Exception as e:
            raise ConnectionError(f"Unexpected error connecting to MongoDB: {e}")
    
    def get_connection(self, session_id: str) -> Optional[MongoClient]:
        """Get MongoDB client for a session."""
        if session_id not in self.connections:
            return None
        
        conn_info = self.connections[session_id]
        
        # Check if connection is still valid
        if time.time() - conn_info['created_at'] > self.session_ttl:
            asyncio.create_task(self.close_connection(session_id))
            return None
        
        # Update last used timestamp
        conn_info['last_used'] = time.time()
        return conn_info['client']
    
    def get_connection_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get connection information for a session."""
        if session_id not in self.connections:
            return None
        
        conn_info = self.connections[session_id]
        return {
            'session_id': session_id,
            'server_info': conn_info['server_info'],
            'parsed_info': conn_info['parsed_info'],
            'created_at': conn_info['created_at'],
            'last_used': conn_info['last_used'],
            'age_seconds': time.time() - conn_info['created_at']
        }
    
    async def close_connection(self, session_id: str) -> bool:
        """Close a specific connection."""
        if session_id not in self.connections:
            return False
        
        try:
            conn_info = self.connections[session_id]
            conn_info['client'].close()
            del self.connections[session_id]
            logger.info(f"Connection closed: {session_id}")
            return True
        except Exception as e:
            logger.error(f"Error closing connection {session_id}: {e}")
            return False
    
    async def cleanup_expired_sessions(self):
        """Remove expired connections."""
        current_time = time.time()
        expired_sessions = []
        
        for session_id, conn_info in self.connections.items():
            if current_time - conn_info['created_at'] > self.session_ttl:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            await self.close_connection(session_id)
        
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired connections")
    
    def list_active_connections(self) -> List[Dict[str, Any]]:
        """List all active connections."""
        current_time = time.time()
        active_connections = []
        
        for session_id, conn_info in self.connections.items():
            if current_time - conn_info['created_at'] <= self.session_ttl:
                info = self.get_connection_info(session_id)
                if info:
                    active_connections.append(info)
        
        return active_connections
    
    async def test_connectivity(self, session_id: str) -> Dict[str, Any]:
        """Test if a connection is still working."""
        client = self.get_connection(session_id)
        if not client:
            return {'status': 'error', 'message': 'Session not found or expired'}
        
        try:
            result = client.admin.command('ping')
            return {
                'status': 'success',
                'ping_result': result,
                'server_status': 'connected'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Connection test failed: {e}'
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection manager statistics."""
        current_time = time.time()
        active_count = sum(
            1 for conn_info in self.connections.values()
            if current_time - conn_info['created_at'] <= self.session_ttl
        )
        
        return {
            'total_connections': len(self.connections),
            'active_connections': active_count,
            'max_connections': self.max_connections,
            'session_ttl': self.session_ttl
        }
    
    async def shutdown(self):
        """Shutdown connection manager and close all connections."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
        
        for session_id in list(self.connections.keys()):
            await self.close_connection(session_id)
        
        logger.info("Connection manager shut down") 