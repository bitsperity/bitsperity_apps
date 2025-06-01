"""
bitsperity-mqtt-mcp - MQTT Tools
Phase 1: Basic MCP Tools für Session Management
Phase 2: Real MQTT Integration mit aiomqtt
Phase 3: Simple Data Optimization mit Message Pruning

Implements 7 MVP tools:
- establish_connection, list_active_connections, close_connection (Phase 1)
- list_topics, subscribe_and_collect, publish_message (Phase 2)  
- get_topic_schema (Phase 3)
"""

import logging
from typing import Dict, Any, List, Optional
import asyncio
from datetime import datetime
import time  # Add time import for performance measurements
import aiomqtt

# Phase 3: Import message optimization classes
from message_pruner import SimpleMessagePruner, SchemaDetector

logger = logging.getLogger(__name__)


class MQTTTools:
    """
    MQTT Tools für MCP Protocol
    
    Phase 1: Basic session management tools ✅
    Phase 2: Real MQTT integration tools ✅
    Phase 3: Simple data optimization tools 🚀
    Phase 4: Advanced tools (future)
    """
    
    def __init__(self, connection_manager):
        """
        Initialize MQTT Tools
        
        Args:
            connection_manager: MQTTConnectionManager instance
        """
        from mqtt_connection_manager import MQTTConnectionManager
        
        self.connection_manager: MQTTConnectionManager = connection_manager
        
        # Phase 3: Initialize optimization components
        self.message_pruner = SimpleMessagePruner(target_count=50)
        self.schema_detector = SchemaDetector()
        
        logger.info("MQTTTools initialized - Phase 3 with Simple Data Optimization")
    
    async def establish_connection(self, connection_string: str, **kwargs) -> Dict[str, Any]:
        """
        Tool: establish_connection
        
        Establishes a new MQTT broker connection with session management.
        
        Args:
            connection_string: MQTT connection string
                Format: mqtt://[username:password@]broker:port[/client_id]
                Examples:
                - mqtt://192.168.178.57:1883
                - mqtt://user:pass@broker.example.com:1883/my_client
                - mqtt://mosquitto_broker_1:1883
        
        Returns:
            Dict containing:
            - session_id: Unique session identifier
            - broker: MQTT broker hostname
            - port: MQTT broker port
            - status: Connection status (connected/failed)
            - created_at: Session creation timestamp
            
        Raises:
            Exception: If connection fails or limits exceeded
        """
        try:
            logger.info(f"Attempting to establish MQTT connection to: {connection_string}")
            
            # Validate connection string format
            if not connection_string.startswith('mqtt://'):
                raise ValueError("Connection string must start with 'mqtt://'")
            
            # Delegate to connection manager
            result = await self.connection_manager.establish_connection(connection_string)
            
            logger.info(f"Successfully established connection: {result['session_id']}")
            
            # Add tool-specific metadata
            result.update({
                'tool': 'establish_connection',
                'description': f"Connected to MQTT broker {result['broker']}:{result['port']}",
                'session_ttl_hours': 1
            })
            
            return result
            
        except Exception as e:
            error_msg = f"Failed to establish MQTT connection: {str(e)}"
            logger.error(error_msg)
            
            return {
                'tool': 'establish_connection',
                'status': 'error',
                'error': error_msg,
                'connection_string': connection_string
            }
    
    async def list_active_connections(self, **kwargs) -> Dict[str, Any]:
        """
        Tool: list_active_connections
        
        Lists all currently active MQTT connections managed by this server.
        
        Returns:
            Dict containing:
            - active_connections: List of connection details
            - total_count: Number of active connections
            - max_connections: Maximum allowed connections
            - timestamp: When this list was generated
            
        Connection details include:
            - session_id: Unique session identifier
            - broker: MQTT broker hostname
            - port: MQTT broker port
            - client_id: MQTT client ID (if specified)
            - created_at: When session was created
            - last_accessed: When session was last used
            - is_connected: Current connection status
            - connection_error: Error message if connection failed
        """
        try:
            logger.debug("Listing active MQTT connections")
            
            # Get connections from manager
            connections_data = self.connection_manager.list_active_connections()
            
            # Add tool-specific metadata
            result = {
                'tool': 'list_active_connections',
                'timestamp': connections_data.get('timestamp'),
                **connections_data
            }
            
            logger.debug(f"Found {result['total_count']} active connections")
            
            return result
            
        except Exception as e:
            error_msg = f"Failed to list active connections: {str(e)}"
            logger.error(error_msg)
            
            return {
                'tool': 'list_active_connections',
                'status': 'error',
                'error': error_msg,
                'active_connections': [],
                'total_count': 0
            }
    
    async def close_connection(self, session_id: str, **kwargs) -> Dict[str, Any]:
        """
        Tool: close_connection
        
        Closes an active MQTT connection and cleans up the session.
        
        Args:
            session_id: Session ID of the connection to close
                      (obtained from establish_connection or list_active_connections)
        
        Returns:
            Dict containing:
            - session_id: The closed session ID
            - status: Closure status (closed/error)
            - closed_at: When the session was closed
            - message: Human-readable status message
            
        Raises:
            Exception: If session not found or closure fails
        """
        try:
            if not session_id:
                raise ValueError("session_id is required")
            
            logger.info(f"Attempting to close MQTT session: {session_id}")
            
            # Delegate to connection manager
            result = await self.connection_manager.close_session(session_id)
            
            logger.info(f"Successfully closed session: {session_id}")
            
            # Add tool-specific metadata
            result.update({
                'tool': 'close_connection',
                'message': f"MQTT session {session_id} closed successfully"
            })
            
            return result
            
        except Exception as e:
            error_msg = f"Failed to close connection {session_id}: {str(e)}"
            logger.error(error_msg)
            
            return {
                'tool': 'close_connection',
                'status': 'error',
                'error': error_msg,
                'session_id': session_id
            }
    
    # Phase 2 Tools (placeholders für spätere Implementation)
    
    async def list_topics(self, session_id: str, pattern: str = "#", **kwargs) -> Dict[str, Any]:
        """
        Tool: list_topics (Phase 2 + Phase 3 Optimization)
        
        Discovers available MQTT topics on the broker by subscribing to wildcard patterns.
        Phase 3: Optimized with smart topic limiting and pattern analysis.
        
        Args:
            session_id: Session ID of an active MQTT connection
            pattern: MQTT topic pattern for discovery (default: "#" for all topics)
                    Examples:
                    - "#" - All topics
                    - "sensor/#" - All topics under sensor/
                    - "device/+/status" - Status topics for all devices
                    - "$SYS/#" - System topics (broker statistics)
        
        Returns:
            Dict containing:
            - session_id: The session ID used
            - pattern: The discovery pattern used
            - topics: List of discovered topic names (optimized)
            - topic_count: Number of unique topics found
            - discovery_duration_seconds: How long discovery took
            - optimization_applied: Whether topic limiting was applied
            - timestamp: When discovery was performed
            
        Raises:
            Exception: If session not found, not connected, or discovery fails
        """
        discovery_start = datetime.now()
        
        try:
            if not session_id:
                raise ValueError("session_id is required")
            
            logger.info(f"Starting topic discovery for session {session_id} with pattern: {pattern}")
            
            # Get session
            session = await self.connection_manager.get_session(session_id)
            if not session:
                raise Exception(f"Session {session_id} not found or expired")
            
            if not session.is_connected or not session.mqtt_client:
                raise Exception(f"Session {session_id} is not connected to MQTT broker")
            
            # Phase 2: Real topic discovery using aiomqtt
            discovered_topics = set()
            
            # Get credentials and create fresh client for this operation
            credentials = session.get_credentials()
            client_id = session.parsed_connection.get('client_id') or f"bitsperity-mqtt-mcp-{session.session_id[:8]}"
            
            client_options = {
                'hostname': session.parsed_connection['broker'],
                'port': session.parsed_connection['port'],
                'identifier': client_id + "-discovery",
                'timeout': 30.0,
                'keepalive': 60,
            }
            
            if credentials['username'] and credentials['password']:
                client_options['username'] = credentials['username']
                client_options['password'] = credentials['password']
            
            # Use fresh client for discovery
            async with aiomqtt.Client(**client_options) as client:
                # Subscribe to discovery pattern
                await client.subscribe(pattern)
                logger.debug(f"Subscribed to discovery pattern: {pattern}")
                
                # Collect topics for a short period (5 seconds)
                discovery_timeout = 5.0
                
                try:
                    # Python 3.10 compatibility - use wait_for instead of timeout
                    async def collect_topics():
                        async for message in client.messages:
                            # Add discovered topic to set
                            discovered_topics.add(message.topic.value)
                            
                            # Phase 3: Smart topic limiting (prevent overwhelming results)
                            if len(discovered_topics) >= 1000:  # Max 1000 topics
                                logger.warning("Topic discovery limit reached (1000 topics)")
                                break
                    
                    await asyncio.wait_for(collect_topics(), timeout=discovery_timeout)
                        
                except asyncio.TimeoutError:
                    # Discovery timeout is expected - this is how we stop collection
                    logger.debug(f"Topic discovery completed after {discovery_timeout}s timeout")
                
                # Unsubscribe from discovery pattern
                await client.unsubscribe(pattern)
            
            # Recreate client for future use (aiomqtt clients are not reusable)
            client_options = {
                'hostname': session.parsed_connection['broker'],
                'port': session.parsed_connection['port'],
                'identifier': client_id,
                'timeout': 30.0,
                'keepalive': 60,
            }
            
            if credentials['username'] and credentials['password']:
                client_options['username'] = credentials['username']
                client_options['password'] = credentials['password']
            
            session.mqtt_client = aiomqtt.Client(**client_options)
            
            discovery_end = datetime.now()
            discovery_duration = (discovery_end - discovery_start).total_seconds()
            
            # Phase 3: Smart topic optimization
            topics_list = sorted(list(discovered_topics))
            optimization_applied = False
            
            # If too many topics, apply smart filtering
            if len(topics_list) > 100:
                # Keep system topics, error topics, and sample of others
                priority_topics = []
                system_topics = []
                regular_topics = []
                
                for topic in topics_list:
                    topic_lower = topic.lower()
                    if any(sys_pattern in topic for sys_pattern in ['$SYS', 'system', 'status']):
                        system_topics.append(topic)
                    elif any(err_pattern in topic_lower for err_pattern in ['error', 'warning', 'alarm', 'alert']):
                        priority_topics.append(topic)
                    else:
                        regular_topics.append(topic)
                
                # Keep all priority and system topics, sample from regular
                optimized_topics = priority_topics + system_topics
                remaining_slots = max(0, 100 - len(optimized_topics))
                
                if remaining_slots > 0 and regular_topics:
                    # Sample evenly from regular topics
                    step = max(1, len(regular_topics) // remaining_slots)
                    sampled_regular = regular_topics[::step][:remaining_slots]
                    optimized_topics.extend(sampled_regular)
                
                topics_list = sorted(optimized_topics)
                optimization_applied = True
                logger.info(f"Applied topic optimization: {len(discovered_topics)} → {len(topics_list)} topics")
            
            logger.info(f"Discovered {len(topics_list)} topics in {discovery_duration:.2f}s")
            
            return {
                'tool': 'list_topics',
                'session_id': session_id,
                'pattern': pattern,
                'topics': topics_list,
                'topic_count': len(topics_list),
                'discovery_duration_seconds': round(discovery_duration, 2),
                'optimization_applied': optimization_applied,
                'timestamp': discovery_end.isoformat(),
                'status': 'success'
            }
            
        except Exception as e:
            error_msg = f"Failed to discover topics: {str(e)}"
            logger.error(error_msg)
            
            discovery_end = datetime.now()
            discovery_duration = (discovery_end - discovery_start).total_seconds()
            
            return {
                'tool': 'list_topics',
                'session_id': session_id,
                'pattern': pattern,
                'status': 'error',
                'error': error_msg,
                'topics': [],
                'topic_count': 0,
                'discovery_duration_seconds': round(discovery_duration, 2),
                'optimization_applied': False,
                'timestamp': discovery_end.isoformat()
            }
    
    async def subscribe_and_collect(self, session_id: str, topic_pattern: str, duration_seconds: int = 30, **kwargs) -> Dict[str, Any]:
        """
        Tool: subscribe_and_collect (Phase 2 + Phase 3 Optimization)
        
        Subscribes to MQTT topic pattern and collects messages for a specified duration.
        Phase 3: Optimized with smart message pruning (500→50 messages).
        
        Args:
            session_id: Session ID of an active MQTT connection
            topic_pattern: MQTT topic pattern to subscribe to
                          Examples:
                          - "sensor/+/temperature" - Temperature from all sensors
                          - "device/pump1/#" - All messages from pump1
                          - "alarm/#" - All alarm messages
            duration_seconds: How long to collect messages (10-300 seconds, default: 30)
        
        Returns:
            Dict containing:
            - session_id: The session ID used
            - topic_pattern: The subscription pattern used
            - messages: List of collected messages (OPTIMIZED - max 50)
            - message_count: Number of messages after optimization
            - original_message_count: Number of messages before optimization
            - collection_duration_seconds: Actual collection time
            - duration_requested: Requested collection duration
            - pruning_applied: Whether message pruning was applied
            - pruning_stats: Details about pruning strategy
            - timestamp: When collection was performed
            
        Each message contains:
            - topic: The message topic
            - payload: The message payload (decoded as string)
            - qos: Quality of Service level
            - retain: Whether message was retained
            - timestamp: When message was received
            
        Raises:
            Exception: If session not found, not connected, or collection fails
        """
        collection_start = datetime.now()
        
        try:
            if not session_id:
                raise ValueError("session_id is required")
            
            if not topic_pattern:
                raise ValueError("topic_pattern is required")
            
            # Validate duration range
            if duration_seconds < 10 or duration_seconds > 300:
                raise ValueError("duration_seconds must be between 10 and 300 seconds")
            
            logger.info(f"Starting message collection for session {session_id}, pattern: {topic_pattern}, duration: {duration_seconds}s")
            
            # Get session
            session = await self.connection_manager.get_session(session_id)
            if not session:
                raise Exception(f"Session {session_id} not found or expired")
            
            if not session.is_connected or not session.mqtt_client:
                raise Exception(f"Session {session_id} is not connected to MQTT broker")
            
            # Phase 2: Real message collection using aiomqtt
            collected_messages = []
            
            # Get credentials and create fresh client for this operation
            credentials = session.get_credentials()
            client_id = session.parsed_connection.get('client_id') or f"bitsperity-mqtt-mcp-{session.session_id[:8]}"
            
            client_options = {
                'hostname': session.parsed_connection['broker'],
                'port': session.parsed_connection['port'],
                'identifier': client_id + "-collection",
                'timeout': 30.0,
                'keepalive': 60,
            }
            
            if credentials['username'] and credentials['password']:
                client_options['username'] = credentials['username']
                client_options['password'] = credentials['password']
            
            # Use fresh client for collection
            async with aiomqtt.Client(**client_options) as client:
                # Subscribe to topic pattern
                await client.subscribe(topic_pattern)
                logger.debug(f"Subscribed to topic pattern: {topic_pattern}")
                
                try:
                    # Python 3.10 compatibility - use wait_for instead of timeout
                    async def collect_messages():
                        async for message in client.messages:
                            # Decode payload safely
                            try:
                                payload_str = message.payload.decode('utf-8')
                            except UnicodeDecodeError:
                                # Handle binary payloads
                                payload_str = f"<binary data: {len(message.payload)} bytes>"
                            
                            # Create message record
                            message_record = {
                                'topic': message.topic.value,
                                'payload': payload_str,
                                'qos': message.qos.value if hasattr(message.qos, 'value') else int(message.qos),
                                'retain': message.retain,
                                'timestamp': datetime.now().isoformat()
                            }
                            
                            collected_messages.append(message_record)
                            
                            # Limit collection to prevent memory issues
                            if len(collected_messages) >= 500:  # Max 500 messages
                                logger.warning("Message collection limit reached (500 messages)")
                                break
                    
                    # Collect messages for specified duration
                    await asyncio.wait_for(collect_messages(), timeout=duration_seconds)
                        
                except asyncio.TimeoutError:
                    # Collection timeout is expected - this is how we stop collection
                    logger.debug(f"Message collection completed after {duration_seconds}s timeout")
                
                # Unsubscribe from topic pattern
                await client.unsubscribe(topic_pattern)
            
            # Recreate client for future use (aiomqtt clients are not reusable)
            client_options = {
                'hostname': session.parsed_connection['broker'],
                'port': session.parsed_connection['port'],
                'identifier': client_id,
                'timeout': 30.0,
                'keepalive': 60,
            }
            
            if credentials['username'] and credentials['password']:
                client_options['username'] = credentials['username']
                client_options['password'] = credentials['password']
            
            session.mqtt_client = aiomqtt.Client(**client_options)
            
            collection_end = datetime.now()
            collection_duration = (collection_end - collection_start).total_seconds()
            
            original_count = len(collected_messages)
            
            # Phase 3: Apply smart message pruning
            pruning_applied = False
            pruning_stats = {}
            optimized_messages = collected_messages
            
            if len(collected_messages) > 50:
                logger.info(f"Applying message pruning: {len(collected_messages)} → max 50 messages")
                
                pruning_result = self.message_pruner.prune_messages(collected_messages, target_count=50)
                optimized_messages = pruning_result['pruned_messages']
                pruning_applied = True
                pruning_stats = pruning_result['pruning_stats']
                
                logger.info(f"Message pruning complete: {original_count} → {len(optimized_messages)} messages "
                           f"({pruning_result['reduction_ratio']}% reduction)")
            
            logger.info(f"Collected {len(optimized_messages)} messages in {collection_duration:.2f}s")
            
            return {
                'tool': 'subscribe_and_collect',
                'session_id': session_id,
                'topic_pattern': topic_pattern,
                'messages': optimized_messages,
                'message_count': len(optimized_messages),
                'original_message_count': original_count,
                'collection_duration_seconds': round(collection_duration, 2),
                'duration_requested': duration_seconds,
                'pruning_applied': pruning_applied,
                'pruning_stats': pruning_stats,
                'timestamp': collection_end.isoformat(),
                'status': 'success'
            }
            
        except Exception as e:
            error_msg = f"Failed to collect messages: {str(e)}"
            logger.error(error_msg)
            
            collection_end = datetime.now()
            collection_duration = (collection_end - collection_start).total_seconds()
            
            return {
                'tool': 'subscribe_and_collect',
                'session_id': session_id,
                'topic_pattern': topic_pattern,
                'status': 'error',
                'error': error_msg,
                'messages': [],
                'message_count': 0,
                'original_message_count': 0,
                'collection_duration_seconds': round(collection_duration, 2),
                'duration_requested': duration_seconds,
                'pruning_applied': False,
                'pruning_stats': {},
                'timestamp': collection_end.isoformat()
            }
    
    async def publish_message(self, session_id: str, topic: str, payload: str, qos: int = 0, retain: bool = False, **kwargs) -> Dict[str, Any]:
        """
        Tool: publish_message (Phase 2)
        
        Publishes a message to an MQTT topic with specified QoS and retain settings.
        
        Args:
            session_id: Session ID of an active MQTT connection
            topic: MQTT topic to publish to (no wildcards allowed)
                  Examples:
                  - "device/pump1/command" - Command to specific device
                  - "sensor/temp1/data" - Data from specific sensor
                  - "alarm/fire/trigger" - Fire alarm trigger
            payload: Message payload as string (will be encoded as UTF-8)
            qos: Quality of Service level (0, 1, or 2, default: 0)
                - 0: Fire and forget (at most once)
                - 1: At least once delivery
                - 2: Exactly once delivery
            retain: Whether broker should retain message for new subscribers (default: False)
        
        Returns:
            Dict containing:
            - session_id: The session ID used
            - topic: The topic published to
            - payload: The published payload
            - payload_size_bytes: Size of payload in bytes
            - qos: Quality of Service level used
            - retain: Whether message was retained
            - publish_duration_seconds: How long publish took
            - timestamp: When message was published
            
        Raises:
            Exception: If session not found, not connected, or publish fails
        """
        publish_start = datetime.now()
        
        try:
            if not session_id:
                raise ValueError("session_id is required")
            
            if not topic:
                raise ValueError("topic is required")
            
            if payload is None:
                raise ValueError("payload is required")
            
            # Validate QoS level
            if qos not in [0, 1, 2]:
                raise ValueError("qos must be 0, 1, or 2")
            
            # Validate topic (no wildcards allowed for publishing)
            if '+' in topic or '#' in topic:
                raise ValueError("Wildcards (+, #) are not allowed in publish topics")
            
            # Validate payload size (limit to 1MB)
            payload_bytes = payload.encode('utf-8')
            if len(payload_bytes) > 1024 * 1024:  # 1MB limit
                raise ValueError("Payload size exceeds 1MB limit")
            
            logger.info(f"Publishing message to topic '{topic}' for session {session_id}, QoS: {qos}, retain: {retain}")
            
            # Get session
            session = await self.connection_manager.get_session(session_id)
            if not session:
                raise Exception(f"Session {session_id} not found or expired")
            
            if not session.is_connected or not session.mqtt_client:
                raise Exception(f"Session {session_id} is not connected to MQTT broker")
            
            # Phase 2: Real message publishing using aiomqtt
            # Get credentials and create fresh client for this operation
            credentials = session.get_credentials()
            client_id = session.parsed_connection.get('client_id') or f"bitsperity-mqtt-mcp-{session.session_id[:8]}"
            
            client_options = {
                'hostname': session.parsed_connection['broker'],
                'port': session.parsed_connection['port'],
                'identifier': client_id + "-publish",
                'timeout': 30.0,
                'keepalive': 60,
            }
            
            if credentials['username'] and credentials['password']:
                client_options['username'] = credentials['username']
                client_options['password'] = credentials['password']
            
            # Use fresh client for publishing
            async with aiomqtt.Client(**client_options) as client:
                # Publish message with specified parameters
                await client.publish(
                    topic=topic,
                    payload=payload_bytes,
                    qos=qos,
                    retain=retain
                )
                
                logger.debug(f"Published {len(payload_bytes)} bytes to '{topic}' with QoS {qos}")
            
            # Recreate client for future use (aiomqtt clients are not reusable)
            client_options = {
                'hostname': session.parsed_connection['broker'],
                'port': session.parsed_connection['port'],
                'identifier': client_id,
                'timeout': 30.0,
                'keepalive': 60,
            }
            
            if credentials['username'] and credentials['password']:
                client_options['username'] = credentials['username']
                client_options['password'] = credentials['password']
            
            session.mqtt_client = aiomqtt.Client(**client_options)
            
            publish_end = datetime.now()
            publish_duration = (publish_end - publish_start).total_seconds()
            
            logger.info(f"Successfully published message to '{topic}' in {publish_duration:.3f}s")
            
            return {
                'tool': 'publish_message',
                'session_id': session_id,
                'topic': topic,
                'payload': payload,
                'payload_size_bytes': len(payload_bytes),
                'qos': qos,
                'retain': retain,
                'publish_duration_seconds': round(publish_duration, 3),
                'timestamp': publish_end.isoformat(),
                'status': 'success'
            }
            
        except Exception as e:
            error_msg = f"Failed to publish message: {str(e)}"
            logger.error(error_msg)
            
            publish_end = datetime.now()
            publish_duration = (publish_end - publish_start).total_seconds()
            
            return {
                'tool': 'publish_message',
                'session_id': session_id,
                'topic': topic,
                'payload': payload,
                'status': 'error',
                'error': error_msg,
                'qos': qos,
                'retain': retain,
                'publish_duration_seconds': round(publish_duration, 3),
                'timestamp': publish_end.isoformat()
            }
    
    # Phase 3 Tools
    
    async def get_topic_schema(self, session_id: str, topic_pattern: str, **kwargs) -> Dict[str, Any]:
        """
        Tool: get_topic_schema (Phase 3)
        
        Analyzes message structures for a topic pattern to detect schema patterns.
        Uses simple pattern recognition to understand message formats.
        
        Args:
            session_id: Session ID of an active MQTT connection
            topic_pattern: MQTT topic pattern to analyze
                          Examples:
                          - "sensor/+/data" - Analyze sensor data structures
                          - "device/pump1/#" - Analyze all pump1 message formats
                          - "alarm/#" - Analyze alarm message schemas
        
        Returns:
            Dict containing:
            - session_id: The session ID used
            - topic_pattern: The pattern analyzed
            - topic_schemas: Schema patterns by topic
            - payload_types: Distribution of payload types (json, text, number, binary)
            - common_fields: Most common JSON fields found
            - schema_summary: High-level schema overview
            - sample_count: Number of messages analyzed
            - analysis_duration_seconds: How long analysis took
            - timestamp: When analysis was performed
            
        Raises:
            Exception: If session not found, not connected, or analysis fails
        """
        analysis_start = datetime.now()
        
        try:
            if not session_id:
                raise ValueError("session_id is required")
            
            if not topic_pattern:
                raise ValueError("topic_pattern is required")
            
            logger.info(f"Starting schema analysis for session {session_id}, pattern: {topic_pattern}")
            
            # Get session
            session = await self.connection_manager.get_session(session_id)
            if not session:
                raise Exception(f"Session {session_id} not found or expired")
            
            if not session.is_connected or not session.mqtt_client:
                raise Exception(f"Session {session_id} is not connected to MQTT broker")
            
            # Collect sample messages for analysis (30 seconds max)
            sample_messages = []
            
            # Get credentials and create fresh client for this operation
            credentials = session.get_credentials()
            client_id = session.parsed_connection.get('client_id') or f"bitsperity-mqtt-mcp-{session.session_id[:8]}"
            
            client_options = {
                'hostname': session.parsed_connection['broker'],
                'port': session.parsed_connection['port'],
                'identifier': client_id + "-schema",
                'timeout': 30.0,
                'keepalive': 60,
            }
            
            if credentials['username'] and credentials['password']:
                client_options['username'] = credentials['username']
                client_options['password'] = credentials['password']
            
            # Use fresh client for schema analysis
            async with aiomqtt.Client(**client_options) as client:
                # Subscribe to topic pattern
                await client.subscribe(topic_pattern)
                logger.debug(f"Subscribed to topic pattern for schema analysis: {topic_pattern}")
                
                # Collect sample messages (shorter duration for schema analysis)
                sample_timeout = 30.0  # 30 seconds max
                
                try:
                    # Python 3.10 compatibility - use wait_for instead of timeout
                    async def collect_schema_samples():
                        async for message in client.messages:
                            # Decode payload safely
                            try:
                                payload_str = message.payload.decode('utf-8')
                            except UnicodeDecodeError:
                                # Handle binary payloads
                                payload_str = f"<binary data: {len(message.payload)} bytes>"
                            
                            # Create message record for analysis
                            message_record = {
                                'topic': message.topic.value,
                                'payload': payload_str,
                                'qos': message.qos.value if hasattr(message.qos, 'value') else int(message.qos),
                                'retain': message.retain,
                                'timestamp': datetime.now().isoformat()
                            }
                            
                            sample_messages.append(message_record)
                            
                            # Limit sample size for performance
                            if len(sample_messages) >= 100:  # Max 100 messages for schema
                                logger.debug("Schema sample limit reached (100 messages)")
                                break
                    
                    await asyncio.wait_for(collect_schema_samples(), timeout=sample_timeout)
                                
                except asyncio.TimeoutError:
                    # Sample timeout is expected
                    logger.debug(f"Schema sampling completed after {sample_timeout}s timeout")
                
                # Unsubscribe from topic pattern
                await client.unsubscribe(topic_pattern)
            
            # Recreate client for future use (aiomqtt clients are not reusable)
            client_options = {
                'hostname': session.parsed_connection['broker'],
                'port': session.parsed_connection['port'],
                'identifier': client_id,
                'timeout': 30.0,
                'keepalive': 60,
            }
            
            if credentials['username'] and credentials['password']:
                client_options['username'] = credentials['username']
                client_options['password'] = credentials['password']
            
            session.mqtt_client = aiomqtt.Client(**client_options)
            
            # Phase 3: Analyze collected messages for schema patterns
            if sample_messages:
                logger.info(f"Analyzing schema for {len(sample_messages)} sample messages")
                schema_result = self.schema_detector.analyze_messages(sample_messages)
            else:
                logger.warning("No messages collected for schema analysis")
                schema_result = {
                    'topic_schemas': {},
                    'payload_types': {},
                    'common_fields': {},
                    'schema_summary': {
                        'total_topics': 0,
                        'total_messages': 0,
                        'dominant_payload_type': 'unknown'
                    },
                    'status': 'no_data',
                    'tool': 'schema_detector'
                }
            
            analysis_end = datetime.now()
            analysis_duration = (analysis_end - analysis_start).total_seconds()
            
            logger.info(f"Schema analysis complete for pattern '{topic_pattern}' in {analysis_duration:.2f}s")
            
            return {
                'tool': 'get_topic_schema',
                'session_id': session_id,
                'topic_pattern': topic_pattern,
                'sample_count': len(sample_messages),
                'analysis_duration_seconds': round(analysis_duration, 2),
                'timestamp': analysis_end.isoformat(),
                'status': 'success',
                **schema_result  # Include all schema analysis results
            }
            
        except Exception as e:
            error_msg = f"Failed to analyze topic schema: {str(e)}"
            logger.error(error_msg)
            
            analysis_end = datetime.now()
            analysis_duration = (analysis_end - analysis_start).total_seconds()
            
            return {
                'tool': 'get_topic_schema',
                'session_id': session_id,
                'topic_pattern': topic_pattern,
                'status': 'error',
                'error': error_msg,
                'sample_count': 0,
                'analysis_duration_seconds': round(analysis_duration, 2),
                'timestamp': analysis_end.isoformat(),
                'topic_schemas': {},
                'payload_types': {},
                'common_fields': {},
                'schema_summary': {}
            }
    
    # Phase 4 Tools
    
    async def debug_device(self, session_id: str, device_id: str, **kwargs) -> Dict[str, Any]:
        """
        Tool: debug_device (Phase 4)
        
        Device-specific monitoring and debugging for MQTT IoT devices.
        Analyzes message patterns, connection status, and error detection.
        
        Args:
            session_id: Session ID of an active MQTT connection
            device_id: Device identifier to debug (used for topic pattern matching)
                      Examples:
                      - "pump1" - Debug device with ID pump1
                      - "sensor_temp_01" - Debug temperature sensor
                      - "gateway_001" - Debug gateway device
        
        Returns:
            Dict containing:
            - session_id: The session ID used
            - device_id: The device being debugged
            - device_topics: Topics associated with this device
            - recent_messages: Recent messages from device (last 50)
            - message_frequency: Messages per minute analysis
            - error_messages: Error/warning messages from device
            - connection_status: Device connectivity analysis
            - debug_summary: High-level device health summary
            - analysis_duration_seconds: How long analysis took
            - timestamp: When debug was performed
            
        Raises:
            Exception: If session not found, not connected, or debug fails
        """
        debug_start = datetime.now()
        
        try:
            if not session_id:
                raise ValueError("session_id is required")
            
            if not device_id:
                raise ValueError("device_id is required")
            
            logger.info(f"Starting device debug for device '{device_id}' on session {session_id}")
            
            # Get session
            session = await self.connection_manager.get_session(session_id)
            if not session:
                raise Exception(f"Session {session_id} not found or expired")
            
            if not session.is_connected or not session.mqtt_client:
                raise Exception(f"Session {session_id} is not connected to MQTT broker")
            
            # Phase 4: Device-specific debugging
            device_topics = []
            recent_messages = []
            error_messages = []
            
            # Pattern 1: Direct device topic patterns
            device_patterns = [
                f"device/{device_id}/#",
                f"{device_id}/#",
                f"*/{device_id}/*",
                f"sensor/{device_id}/#",
                f"actuator/{device_id}/#"
            ]
            
            # Get credentials and create fresh client for device debugging
            credentials = session.get_credentials()
            client_id = session.parsed_connection.get('client_id') or f"bitsperity-mqtt-mcp-{session.session_id[:8]}"
            
            client_options = {
                'hostname': session.parsed_connection['broker'],
                'port': session.parsed_connection['port'],
                'identifier': client_id + "-debug",
                'timeout': 30.0,
                'keepalive': 60,
            }
            
            if credentials['username'] and credentials['password']:
                client_options['username'] = credentials['username']
                client_options['password'] = credentials['password']
            
            # Use fresh client for device debugging
            async with aiomqtt.Client(**client_options) as client:
                # Subscribe to potential device patterns
                for pattern in device_patterns:
                    try:
                        await client.subscribe(pattern)
                        logger.debug(f"Subscribed to device pattern: {pattern}")
                    except Exception as e:
                        logger.debug(f"Failed to subscribe to {pattern}: {e}")
                
                # Collect device messages for analysis (30 seconds)
                debug_timeout = 30.0
                
                try:
                    # Python 3.10 compatibility - use wait_for instead of timeout
                    async def collect_device_messages():
                        async for message in client.messages:
                            # Check if message is related to device
                            topic = message.topic.value
                            if device_id.lower() in topic.lower():
                                # Decode payload safely
                                try:
                                    payload_str = message.payload.decode('utf-8')
                                except UnicodeDecodeError:
                                    payload_str = f"<binary data: {len(message.payload)} bytes>"
                                
                                # Create message record
                                message_record = {
                                    'topic': topic,
                                    'payload': payload_str,
                                    'qos': message.qos.value if hasattr(message.qos, 'value') else int(message.qos),
                                    'retain': message.retain,
                                    'timestamp': datetime.now().isoformat()
                                }
                                
                                recent_messages.append(message_record)
                                device_topics.append(topic)
                                
                                # Check for error messages
                                if self.message_pruner._is_error_message(message_record):
                                    error_messages.append(message_record)
                                
                                # Limit collection
                                if len(recent_messages) >= 100:
                                    logger.debug("Device debug message limit reached (100 messages)")
                                    break
                    
                    await asyncio.wait_for(collect_device_messages(), timeout=debug_timeout)
                                
                except asyncio.TimeoutError:
                    # Debug timeout is expected
                    logger.debug(f"Device debug completed after {debug_timeout}s timeout")
                
                # Unsubscribe from all patterns
                for pattern in device_patterns:
                    try:
                        await client.unsubscribe(pattern)
                    except Exception:
                        pass
            
            # Recreate client for future use
            client_options = {
                'hostname': session.parsed_connection['broker'],
                'port': session.parsed_connection['port'],
                'identifier': client_id,
                'timeout': 30.0,
                'keepalive': 60,
            }
            
            if credentials['username'] and credentials['password']:
                client_options['username'] = credentials['username']
                client_options['password'] = credentials['password']
            
            session.mqtt_client = aiomqtt.Client(**client_options)
            
            debug_end = datetime.now()
            debug_duration = (debug_end - debug_start).total_seconds()
            
            # Analyze collected data
            unique_topics = list(set(device_topics))
            
            # Message frequency analysis (messages per minute)
            if recent_messages:
                time_span_minutes = debug_duration / 60.0
                message_frequency = len(recent_messages) / time_span_minutes if time_span_minutes > 0 else 0
            else:
                message_frequency = 0
            
            # Connection status analysis
            if recent_messages:
                connection_status = "active"
                last_message_time = recent_messages[-1]['timestamp']
            elif unique_topics:
                connection_status = "topics_found_no_messages"
                last_message_time = None
            else:
                connection_status = "no_activity_detected"
                last_message_time = None
            
            # Debug summary
            debug_summary = {
                'device_health': 'healthy' if error_messages == [] and recent_messages else 'issues_detected' if error_messages else 'inactive',
                'message_activity': 'high' if message_frequency > 10 else 'medium' if message_frequency > 1 else 'low',
                'topic_diversity': len(unique_topics),
                'error_count': len(error_messages),
                'total_messages': len(recent_messages)
            }
            
            # Apply message pruning for response optimization
            if len(recent_messages) > 50:
                pruning_result = self.message_pruner.prune_messages(recent_messages, target_count=50)
                optimized_messages = pruning_result['pruned_messages']
                pruning_applied = True
            else:
                optimized_messages = recent_messages
                pruning_applied = False
            
            logger.info(f"Device debug complete for '{device_id}': {len(optimized_messages)} messages, {len(error_messages)} errors")
            
            return {
                'tool': 'debug_device',
                'session_id': session_id,
                'device_id': device_id,
                'device_topics': unique_topics,
                'recent_messages': optimized_messages,
                'message_frequency_per_minute': round(message_frequency, 2),
                'error_messages': error_messages,
                'connection_status': connection_status,
                'last_message_time': last_message_time,
                'debug_summary': debug_summary,
                'pruning_applied': pruning_applied,
                'analysis_duration_seconds': round(debug_duration, 2),
                'timestamp': debug_end.isoformat(),
                'status': 'success'
            }
            
        except Exception as e:
            error_msg = f"Failed to debug device: {str(e)}"
            logger.error(error_msg)
            
            debug_end = datetime.now()
            debug_duration = (debug_end - debug_start).total_seconds()
            
            return {
                'tool': 'debug_device',
                'session_id': session_id,
                'device_id': device_id,
                'status': 'error',
                'error': error_msg,
                'analysis_duration_seconds': round(debug_duration, 2),
                'timestamp': debug_end.isoformat(),
                'device_topics': [],
                'recent_messages': [],
                'error_messages': []
            }
    
    async def monitor_performance(self, session_id: str, **kwargs) -> Dict[str, Any]:
        """
        Tool: monitor_performance (Phase 4)
        
        Monitors MQTT connection and broker performance metrics.
        Measures throughput, latency, memory usage, and connection health.
        
        Args:
            session_id: Session ID of an active MQTT connection
        
        Returns:
            Dict containing:
            - session_id: The session ID monitored
            - connection_info: Broker connection details
            - throughput_metrics: Messages per second measurements
            - latency_metrics: Publish-to-receive timing analysis
            - memory_metrics: Current memory usage statistics
            - broker_metrics: Broker-specific performance data
            - session_metrics: Session pool and connection status
            - performance_summary: High-level performance assessment
            - monitoring_duration_seconds: How long monitoring took
            - timestamp: When monitoring was performed
            
        Raises:
            Exception: If session not found, not connected, or monitoring fails
        """
        monitor_start = datetime.now()
        
        try:
            if not session_id:
                raise ValueError("session_id is required")
            
            logger.info(f"Starting performance monitoring for session {session_id}")
            
            # Get session
            session = await self.connection_manager.get_session(session_id)
            if not session:
                raise Exception(f"Session {session_id} not found or expired")
            
            if not session.is_connected or not session.mqtt_client:
                raise Exception(f"Session {session_id} is not connected to MQTT broker")
            
            # Phase 4: Performance monitoring
            import psutil
            import time
            
            # Get initial memory snapshot
            process = psutil.Process()
            memory_before = process.memory_info()
            
            # Connection info
            connection_info = {
                'broker': session.parsed_connection['broker'],
                'port': session.parsed_connection['port'],
                'client_id': session.parsed_connection.get('client_id', 'auto-generated'),
                'session_created': session.created_at.isoformat(),
                'session_age_minutes': (datetime.now() - session.created_at).total_seconds() / 60.0
            }
            
            # Throughput test - publish and measure
            test_messages = []
            publish_times = []
            receive_times = []
            
            # Get credentials and create fresh client for performance testing
            credentials = session.get_credentials()
            client_id = session.parsed_connection.get('client_id') or f"bitsperity-mqtt-mcp-{session.session_id[:8]}"
            
            client_options = {
                'hostname': session.parsed_connection['broker'],
                'port': session.parsed_connection['port'],
                'identifier': client_id + "-perf",
                'timeout': 30.0,
                'keepalive': 60,
            }
            
            if credentials['username'] and credentials['password']:
                client_options['username'] = credentials['username']
                client_options['password'] = credentials['password']
            
            # Performance testing
            async with aiomqtt.Client(**client_options) as client:
                test_topic = f"test/performance/{session.session_id}"
                
                # Subscribe to test topic
                await client.subscribe(test_topic)
                
                # Throughput test - send 10 test messages
                throughput_start = time.time()
                
                for i in range(10):
                    test_payload = f"performance_test_message_{i}_{time.time()}"
                    publish_time = time.time()
                    
                    await client.publish(test_topic, test_payload, qos=1)
                    publish_times.append(publish_time)
                    test_messages.append(test_payload)
                
                # Collect responses for latency measurement
                collected_responses = 0
                
                try:
                    async def collect_test_responses():
                        nonlocal collected_responses
                        async for message in client.messages:
                            if message.topic.value == test_topic:
                                receive_time = time.time()
                                payload = message.payload.decode('utf-8')
                                
                                if payload in test_messages:
                                    receive_times.append(receive_time)
                                    collected_responses += 1
                                    
                                    if collected_responses >= len(test_messages):
                                        break
                    
                    # Wait for responses (max 10 seconds)
                    await asyncio.wait_for(collect_test_responses(), timeout=10.0)
                    
                except asyncio.TimeoutError:
                    logger.debug("Performance test timeout - some messages may not have been received")
                
                throughput_end = time.time()
                await client.unsubscribe(test_topic)
            
            # Recreate client for future use
            client_options = {
                'hostname': session.parsed_connection['broker'],
                'port': session.parsed_connection['port'],
                'identifier': client_id,
                'timeout': 30.0,
                'keepalive': 60,
            }
            
            if credentials['username'] and credentials['password']:
                client_options['username'] = credentials['username']
                client_options['password'] = credentials['password']
            
            session.mqtt_client = aiomqtt.Client(**client_options)
            
            # Calculate metrics
            throughput_duration = throughput_end - throughput_start
            messages_sent = len(publish_times)
            messages_received = len(receive_times)
            
            # Throughput metrics
            throughput_metrics = {
                'messages_per_second_sent': round(messages_sent / throughput_duration, 2) if throughput_duration > 0 else 0,
                'messages_per_second_received': round(messages_received / throughput_duration, 2) if throughput_duration > 0 else 0,
                'message_loss_rate': round((messages_sent - messages_received) / messages_sent * 100, 2) if messages_sent > 0 else 0,
                'test_duration_seconds': round(throughput_duration, 3)
            }
            
            # Latency metrics
            if publish_times and receive_times:
                latencies = [r - p for r, p in zip(receive_times[:len(publish_times)], publish_times)]
                latency_metrics = {
                    'average_latency_ms': round(sum(latencies) / len(latencies) * 1000, 2),
                    'min_latency_ms': round(min(latencies) * 1000, 2),
                    'max_latency_ms': round(max(latencies) * 1000, 2),
                    'samples': len(latencies)
                }
            else:
                latency_metrics = {
                    'average_latency_ms': 0,
                    'min_latency_ms': 0,
                    'max_latency_ms': 0,
                    'samples': 0
                }
            
            # Memory metrics
            memory_after = process.memory_info()
            memory_metrics = {
                'current_memory_mb': round(memory_after.rss / 1024 / 1024, 2),
                'memory_change_mb': round((memory_after.rss - memory_before.rss) / 1024 / 1024, 2),
                'peak_memory_mb': round(process.memory_info().rss / 1024 / 1024, 2)
            }
            
            # Session metrics
            all_sessions = self.connection_manager.list_active_connections()
            session_metrics = {
                'active_sessions': all_sessions['total_count'],
                'max_sessions': all_sessions['max_connections'],
                'session_utilization_percent': round(all_sessions['total_count'] / all_sessions['max_connections'] * 100, 2)
            }
            
            # Performance summary
            performance_summary = {
                'overall_health': 'excellent' if throughput_metrics['messages_per_second_sent'] > 5 and latency_metrics['average_latency_ms'] < 100 else 'good' if throughput_metrics['messages_per_second_sent'] > 1 else 'degraded',
                'throughput_rating': 'high' if throughput_metrics['messages_per_second_sent'] > 10 else 'medium' if throughput_metrics['messages_per_second_sent'] > 1 else 'low',
                'latency_rating': 'excellent' if latency_metrics['average_latency_ms'] < 50 else 'good' if latency_metrics['average_latency_ms'] < 200 else 'high',
                'memory_efficiency': 'excellent' if memory_metrics['current_memory_mb'] < 64 else 'good' if memory_metrics['current_memory_mb'] < 128 else 'high'
            }
            
            monitor_end = datetime.now()
            monitor_duration = (monitor_end - monitor_start).total_seconds()
            
            logger.info(f"Performance monitoring complete: {throughput_metrics['messages_per_second_sent']} msg/s, {latency_metrics['average_latency_ms']} ms latency")
            
            return {
                'tool': 'monitor_performance',
                'session_id': session_id,
                'connection_info': connection_info,
                'throughput_metrics': throughput_metrics,
                'latency_metrics': latency_metrics,
                'memory_metrics': memory_metrics,
                'session_metrics': session_metrics,
                'performance_summary': performance_summary,
                'monitoring_duration_seconds': round(monitor_duration, 2),
                'timestamp': monitor_end.isoformat(),
                'status': 'success'
            }
            
        except Exception as e:
            error_msg = f"Failed to monitor performance: {str(e)}"
            logger.error(error_msg)
            
            monitor_end = datetime.now()
            monitor_duration = (monitor_end - monitor_start).total_seconds()
            
            return {
                'tool': 'monitor_performance',
                'session_id': session_id,
                'status': 'error',
                'error': error_msg,
                'monitoring_duration_seconds': round(monitor_duration, 2),
                'timestamp': monitor_end.isoformat()
            }
    
    async def test_connection(self, session_id: str, **kwargs) -> Dict[str, Any]:
        """
        Tool: test_connection (Phase 4)
        
        Comprehensive connection health check and diagnostics for MQTT broker.
        Tests reachability, authentication, QoS levels, and network performance.
        
        Args:
            session_id: Session ID of an active MQTT connection
        
        Returns:
            Dict containing:
            - session_id: The session ID tested
            - broker_info: Broker connection details
            - connectivity_test: Basic reachability results
            - authentication_test: Auth verification results
            - qos_tests: QoS level functionality tests
            - network_diagnostics: Latency and throughput tests
            - broker_diagnostics: Broker-specific health checks
            - overall_health: Comprehensive health assessment
            - test_duration_seconds: How long testing took
            - timestamp: When testing was performed
            
        Raises:
            Exception: If session not found or testing fails
        """
        test_start = datetime.now()
        
        try:
            if not session_id:
                raise ValueError("session_id is required")
            
            logger.info(f"Starting connection test for session {session_id}")
            
            # Get session
            session = await self.connection_manager.get_session(session_id)
            if not session:
                raise Exception(f"Session {session_id} not found or expired")
            
            # Phase 4: Comprehensive connection testing
            
            # Broker info
            broker_info = {
                'broker': session.parsed_connection['broker'],
                'port': session.parsed_connection['port'],
                'client_id': session.parsed_connection.get('client_id', 'auto-generated'),
                'session_active': session.is_connected,
                'session_age_minutes': (datetime.now() - session.created_at).total_seconds() / 60.0
            }
            
            test_results = {
                'connectivity_test': {},
                'authentication_test': {},
                'qos_tests': {},
                'network_diagnostics': {},
                'broker_diagnostics': {}
            }
            
            # Test 1: Basic connectivity
            connectivity_start = time.time()
            
            try:
                # Get credentials for testing
                credentials = session.get_credentials()
                client_id = session.parsed_connection.get('client_id') or f"bitsperity-mqtt-mcp-{session.session_id[:8]}"
                
                client_options = {
                    'hostname': session.parsed_connection['broker'],
                    'port': session.parsed_connection['port'],
                    'identifier': client_id + "-test",
                    'timeout': 10.0,
                    'keepalive': 60,
                }
                
                if credentials['username'] and credentials['password']:
                    client_options['username'] = credentials['username']
                    client_options['password'] = credentials['password']
                
                # Test basic connection
                async with aiomqtt.Client(**client_options) as test_client:
                    connectivity_time = time.time() - connectivity_start
                    
                    test_results['connectivity_test'] = {
                        'status': 'success',
                        'connection_time_ms': round(connectivity_time * 1000, 2),
                        'broker_reachable': True
                    }
                    
                    # Test 2: Authentication (already verified by successful connection)
                    test_results['authentication_test'] = {
                        'status': 'success',
                        'credentials_valid': True,
                        'auth_method': 'username_password' if credentials['username'] else 'anonymous'
                    }
                    
                    # Test 3: QoS levels
                    qos_results = {}
                    test_topic = f"test/connection/{session.session_id}"
                    
                    for qos_level in [0, 1, 2]:
                        try:
                            qos_start = time.time()
                            
                            # Subscribe with QoS
                            await test_client.subscribe(test_topic, qos=qos_level)
                            
                            # Publish test message
                            test_payload = f"qos_test_{qos_level}_{time.time()}"
                            await test_client.publish(test_topic, test_payload, qos=qos_level)
                            
                            # Try to receive the message
                            message_received = False
                            
                            try:
                                async def check_qos_message():
                                    nonlocal message_received
                                    async for message in test_client.messages:
                                        if (message.topic.value == test_topic and 
                                            message.payload.decode('utf-8') == test_payload):
                                            message_received = True
                                            break
                                
                                await asyncio.wait_for(check_qos_message(), timeout=5.0)
                                
                            except asyncio.TimeoutError:
                                pass
                            
                            qos_time = time.time() - qos_start
                            
                            qos_results[f'qos_{qos_level}'] = {
                                'status': 'success' if message_received else 'timeout',
                                'message_received': message_received,
                                'response_time_ms': round(qos_time * 1000, 2)
                            }
                            
                            await test_client.unsubscribe(test_topic)
                            
                        except Exception as e:
                            qos_results[f'qos_{qos_level}'] = {
                                'status': 'error',
                                'error': str(e),
                                'message_received': False
                            }
                    
                    test_results['qos_tests'] = qos_results
                    
                    # Test 4: Network diagnostics
                    network_start = time.time()
                    ping_times = []
                    
                    for i in range(5):
                        ping_start = time.time()
                        ping_topic = f"test/ping/{session.session_id}/{i}"
                        await test_client.publish(ping_topic, f"ping_{i}", qos=0)
                        ping_time = time.time() - ping_start
                        ping_times.append(ping_time)
                    
                    network_time = time.time() - network_start
                    
                    test_results['network_diagnostics'] = {
                        'average_ping_ms': round(sum(ping_times) / len(ping_times) * 1000, 2) if ping_times else 0,
                        'min_ping_ms': round(min(ping_times) * 1000, 2) if ping_times else 0,
                        'max_ping_ms': round(max(ping_times) * 1000, 2) if ping_times else 0,
                        'total_test_time_ms': round(network_time * 1000, 2),
                        'network_stable': all(t < 1.0 for t in ping_times)  # All pings under 1 second
                    }
                    
                    # Test 5: Broker diagnostics (subscribe to $SYS topics if available)
                    broker_diag_start = time.time()
                    broker_info_collected = {}
                    
                    try:
                        sys_topics = [
                            "$SYS/broker/version",
                            "$SYS/broker/uptime",
                            "$SYS/broker/clients/connected",
                            "$SYS/broker/messages/received"
                        ]
                        
                        for sys_topic in sys_topics:
                            try:
                                await test_client.subscribe(sys_topic)
                            except Exception:
                                pass  # Some brokers don't support $SYS topics
                        
                        # Collect $SYS information for 3 seconds
                        try:
                            async def collect_broker_info():
                                async for message in test_client.messages:
                                    topic = message.topic.value
                                    if topic.startswith("$SYS/"):
                                        try:
                                            payload = message.payload.decode('utf-8')
                                            broker_info_collected[topic] = payload
                                        except Exception:
                                            pass
                                        
                                        if len(broker_info_collected) >= 4:
                                            break
                            
                            await asyncio.wait_for(collect_broker_info(), timeout=3.0)
                            
                        except asyncio.TimeoutError:
                            pass
                        
                        # Unsubscribe from $SYS topics
                        for sys_topic in sys_topics:
                            try:
                                await test_client.unsubscribe(sys_topic)
                            except Exception:
                                pass
                        
                    except Exception as e:
                        logger.debug(f"Broker diagnostics error: {e}")
                    
                    broker_diag_time = time.time() - broker_diag_start
                    
                    test_results['broker_diagnostics'] = {
                        'sys_topics_available': len(broker_info_collected) > 0,
                        'broker_info': broker_info_collected,
                        'diagnostics_time_ms': round(broker_diag_time * 1000, 2)
                    }
                
                # Recreate main client for future use
                client_options = {
                    'hostname': session.parsed_connection['broker'],
                    'port': session.parsed_connection['port'],
                    'identifier': client_id,
                    'timeout': 30.0,
                    'keepalive': 60,
                }
                
                if credentials['username'] and credentials['password']:
                    client_options['username'] = credentials['username']
                    client_options['password'] = credentials['password']
                
                session.mqtt_client = aiomqtt.Client(**client_options)
                
            except Exception as e:
                connectivity_time = time.time() - connectivity_start
                test_results['connectivity_test'] = {
                    'status': 'error',
                    'error': str(e),
                    'connection_time_ms': round(connectivity_time * 1000, 2),
                    'broker_reachable': False
                }
                
                test_results['authentication_test'] = {
                    'status': 'error',
                    'error': 'Could not test authentication due to connectivity failure'
                }
            
            test_end = datetime.now()
            test_duration = (test_end - test_start).total_seconds()
            
            # Overall health assessment
            connectivity_ok = test_results['connectivity_test'].get('status') == 'success'
            auth_ok = test_results['authentication_test'].get('status') == 'success'
            qos_working = any(result.get('status') == 'success' for result in test_results['qos_tests'].values()) if test_results['qos_tests'] else False
            network_ok = test_results['network_diagnostics'].get('network_stable', False) if test_results['network_diagnostics'] else False
            
            if connectivity_ok and auth_ok and qos_working and network_ok:
                overall_health = 'excellent'
            elif connectivity_ok and auth_ok and qos_working:
                overall_health = 'good'
            elif connectivity_ok and auth_ok:
                overall_health = 'fair'
            else:
                overall_health = 'poor'
            
            logger.info(f"Connection test complete: overall health = {overall_health}")
            
            return {
                'tool': 'test_connection',
                'session_id': session_id,
                'broker_info': broker_info,
                'connectivity_test': test_results['connectivity_test'],
                'authentication_test': test_results['authentication_test'],
                'qos_tests': test_results['qos_tests'],
                'network_diagnostics': test_results['network_diagnostics'],
                'broker_diagnostics': test_results['broker_diagnostics'],
                'overall_health': overall_health,
                'test_duration_seconds': round(test_duration, 2),
                'timestamp': test_end.isoformat(),
                'status': 'success'
            }
            
        except Exception as e:
            error_msg = f"Failed to test connection: {str(e)}"
            logger.error(error_msg)
            
            test_end = datetime.now()
            test_duration = (test_end - test_start).total_seconds()
            
            return {
                'tool': 'test_connection',
                'session_id': session_id,
                'status': 'error',
                'error': error_msg,
                'test_duration_seconds': round(test_duration, 2),
                'timestamp': test_end.isoformat()
            } 