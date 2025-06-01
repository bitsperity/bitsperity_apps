# bitsperity-mqtt-mcp - Component Design

## Component Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     MQTT MCP Server                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  MCP Protocol   │  │ Connection Mgmt │  │ MQTT Tools      │ │
│  │   Handler       │  │                 │  │                 │ │
│  ├─────────────────┤  ├─────────────────┤  ├─────────────────┤ │
│  │ • JSON-RPC 2.0  │◄─┤ • Session Store │◄─┤ • Topic Monitor │ │
│  │ • Tool Registry │  │ • Client Pool   │  │ • Message Coll  │ │
│  │ • Error Handler │  │ • Auto Cleanup  │  │ • Publisher     │ │
│  │ • STDIO Comm    │  │ • Security      │  │ • Schema Analysis│ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│           │                      │                      │     │
│           ▼                      ▼                      ▼     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ Message Pruner  │  │ MQTT Client     │  │ Web Monitor     │ │
│  │                 │  │ (aiomqtt)       │  │ (FastAPI)       │ │
│  ├─────────────────┤  ├─────────────────┤  ├─────────────────┤ │
│  │ • AI Optimizer  │  │ • Async Client  │  │ • Status API    │ │
│  │ • Diversity     │  │ • QoS Support   │  │ • Session Info  │ │
│  │ • Temporal Dist │  │ • Reconnection  │  │ • Live Logs     │ │
│  │ • Error Priority│  │ • Topic Patterns│  │ • Message Stats │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. SimpleMCPServer (Main Orchestrator)

```python
class SimpleMCPServer:
    """Main MCP Server handling JSON-RPC 2.0 protocol."""
    
    def __init__(self):
        self.connection_manager = MQTTConnectionManager(
            session_ttl=int(os.getenv('SESSION_TTL', '3600')),
            max_connections=int(os.getenv('MAX_CONNECTIONS', '5'))
        )
        self.mqtt_tools = MQTTTools(self.connection_manager)
        self.message_pruner = MessagePruner()
    
    async def handle_request(self, request_data: str) -> dict:
        """Handle incoming JSON-RPC 2.0 requests."""
        
    async def run(self) -> None:
        """Main STDIO communication loop."""
        
    def _get_tool_definitions(self) -> List[dict]:
        """Return MCP tool schema definitions."""
```

**Responsibilities:**
- JSON-RPC 2.0 protocol handling
- Tool registration and execution
- Error handling and response formatting
- STDIO communication management

### 2. MQTTConnectionManager (Session & Security)

```python
class MQTTConnectionManager:
    """Manages MQTT connections with security and session lifecycle."""
    
    def __init__(self, session_ttl: int = 3600, max_connections: int = 5):
        self.session_ttl = session_ttl
        self.max_connections = max_connections
        self.connections: Dict[str, MQTTSession] = {}
        self.cipher_suite = Fernet(Fernet.generate_key())
    
    async def establish_connection(self, connection_string: str) -> str:
        """Create new MQTT connection and return session ID."""
        
    async def get_client(self, session_id: str) -> Optional[aiomqtt.Client]:
        """Get MQTT client for session."""
        
    async def close_connection(self, session_id: str) -> bool:
        """Close specific MQTT connection."""
        
    async def cleanup_expired_sessions(self) -> None:
        """Remove expired connections."""
        
    def list_active_connections(self) -> List[dict]:
        """List all active MQTT sessions."""

class MQTTSession:
    """Individual MQTT connection session."""
    
    def __init__(self, session_id: str, client: aiomqtt.Client, broker_info: dict):
        self.session_id = session_id
        self.client = client
        self.broker_info = broker_info
        self.created_at = time.time()
        self.last_used = time.time()
        self.message_count = 0
        self.subscriptions: Set[str] = set()
```

**Responsibilities:**
- Session lifecycle management
- MQTT client connection pooling  
- Security (credential encryption, session isolation)
- Resource limits and cleanup
- Connection health monitoring

### 3. MQTTTools (Core Functionality)

```python
class MQTTTools:
    """MQTT-specific tools for AI assistant interaction."""
    
    def __init__(self, connection_manager: MQTTConnectionManager):
        self.connection_manager = connection_manager
        self.message_pruner = MessagePruner()
    
    # MVP Tools
    async def establish_connection(self, connection_string: str) -> dict:
        """Tool: Connect to MQTT broker."""
        
    async def list_topics(self, session_id: str, pattern: str = "#", 
                         duration: int = 30) -> dict:
        """Tool: Discover available topics using wildcards."""
        
    async def subscribe_and_collect(self, session_id: str, topic: str,
                                   duration: int = 30, max_messages: int = 100,
                                   qos: int = 0) -> dict:
        """Tool: Collect messages from topic for specified time."""
        
    async def publish_message(self, session_id: str, topic: str, payload: str,
                             qos: int = 0, retain: bool = False) -> dict:
        """Tool: Publish message to MQTT topic."""
        
    def list_active_connections(self) -> dict:
        """Tool: List all active MQTT sessions."""
        
    async def close_connection(self, session_id: str) -> dict:
        """Tool: Close MQTT connection."""
    
    # Advanced Tools (Phase 2)
    async def get_topic_schema(self, session_id: str, topic: str,
                              duration: int = 60) -> dict:
        """Tool: Analyze message structure and generate schema."""
        
    async def debug_device(self, session_id: str, device_pattern: str,
                          duration: int = 120) -> dict:
        """Tool: Debug device-specific MQTT communication."""
        
    async def monitor_performance(self, session_id: str, topics: List[str],
                                 duration: int = 300) -> dict:
        """Tool: Monitor MQTT performance metrics."""
        
    async def test_connection(self, session_id: str) -> dict:
        """Tool: Test MQTT connection health."""
```

**Responsibilities:**
- Implementation of all MCP tools
- MQTT protocol operations (subscribe, publish, discovery)
- Tool parameter validation
- Result formatting for AI assistant

### 4. MessageCollector (Real-time Processing)

```python
class MessageCollector:
    """Real-time MQTT message collection with limits."""
    
    def __init__(self, max_messages: int = 100, duration: int = 30):
        self.max_messages = max_messages
        self.duration = duration
        self.messages: List[MQTTMessage] = []
        self.start_time = time.time()
        self.topics_seen: Set[str] = set()
    
    async def collect_from_topic(self, client: aiomqtt.Client, 
                                topic_pattern: str, qos: int = 0) -> dict:
        """Collect messages from topic with stop conditions."""
        
    async def discover_topics(self, client: aiomqtt.Client,
                             pattern: str = "#", duration: int = 30) -> dict:
        """Discover available topics using wildcards."""
        
    def should_stop(self) -> bool:
        """Check if collection should stop."""
        
    def get_statistics(self) -> dict:
        """Get collection statistics."""

class MQTTMessage:
    """Individual MQTT message with metadata."""
    
    def __init__(self, topic: str, payload: bytes, qos: int, 
                 retain: bool, timestamp: float):
        self.topic = topic
        self.payload = payload
        self.qos = qos
        self.retain = retain
        self.timestamp = timestamp
        self.size_bytes = len(payload)
        self.payload_type = self._detect_payload_type()
    
    def _detect_payload_type(self) -> str:
        """Detect payload format (json, xml, binary, text)."""
        
    def to_dict(self) -> dict:
        """Convert message to dictionary for JSON response."""
```

**Responsibilities:**
- Real-time message collection
- Topic discovery with wildcards
- Stop condition management (time and count limits)
- Message metadata extraction
- Payload type detection

### 5. MessagePruner (AI Optimization)

```python
class MessagePruner:
    """Intelligent message pruning for AI assistant processing."""
    
    def __init__(self, target_size: int = 50):
        self.target_size = target_size
    
    def prune_messages(self, messages: List[MQTTMessage]) -> dict:
        """Reduce message list for optimal AI processing."""
        
    def _prioritize_messages(self, messages: List[MQTTMessage]) -> List[MQTTMessage]:
        """Sort messages by importance for AI analysis."""
        
    def _temporal_sample(self, messages: List[MQTTMessage], 
                        target_count: int) -> List[MQTTMessage]:
        """Sample messages uniformly across time period."""
        
    def _preserve_diversity(self, messages: List[MQTTMessage],
                           target_count: int) -> List[MQTTMessage]:
        """Preserve messages with different payload structures."""
        
    def _is_error_message(self, message: MQTTMessage) -> bool:
        """Detect if message contains error or warning information."""
        
    def generate_pruning_summary(self, original_count: int, 
                                final_count: int, strategy: str) -> dict:
        """Generate summary of pruning operation."""
```

**Responsibilities:**
- Reduce large message collections to manageable size
- Preserve important messages (errors, first/last, diversity)
- Temporal distribution sampling
- Pruning summary generation

### 6. SchemaAnalyzer (Message Structure)

```python
class SchemaAnalyzer:
    """Analyze MQTT message structures and generate schemas."""
    
    def __init__(self):
        self.format_detectors = {
            'json': self._analyze_json,
            'xml': self._analyze_xml,
            'binary': self._analyze_binary,
            'text': self._analyze_text
        }
    
    def analyze_topic(self, messages: List[MQTTMessage]) -> dict:
        """Analyze message patterns for a topic."""
        
    def _analyze_json(self, messages: List[MQTTMessage]) -> dict:
        """Generate JSON schema from message samples."""
        
    def _analyze_xml(self, messages: List[MQTTMessage]) -> dict:
        """Analyze XML structure patterns."""
        
    def _analyze_binary(self, messages: List[MQTTMessage]) -> dict:
        """Analyze binary message characteristics."""
        
    def _analyze_text(self, messages: List[MQTTMessage]) -> dict:
        """Analyze plain text message patterns."""
        
    def _detect_message_format(self, payload: bytes) -> str:
        """Detect payload format type."""
        
    def generate_schema_confidence(self, sample_size: int) -> str:
        """Calculate schema confidence based on sample size."""
```

**Responsibilities:**
- Message format detection (JSON, XML, binary, text)
- JSON schema generation
- Pattern analysis across message samples
- Schema confidence calculation

### 7. WebMonitor (Status Interface)

```python
class WebMonitor:
    """FastAPI web interface for monitoring MCP server."""
    
    def __init__(self, mcp_server: SimpleMCPServer):
        self.mcp_server = mcp_server
        self.app = FastAPI(title="MQTT MCP Monitor")
        self.setup_routes()
    
    def setup_routes(self):
        """Setup FastAPI routes."""
        
    @self.app.get("/health")
    async def health_check():
        """Health check endpoint."""
        
    @self.app.get("/api/sessions")
    async def get_sessions():
        """Get active MQTT sessions."""
        
    @self.app.get("/api/stats")
    async def get_stats():
        """Get server statistics."""
        
    @self.app.post("/api/log-call")
    async def log_mcp_call(call_data: dict):
        """Log MCP tool call for monitoring."""
        
    async def run(self, host: str = "0.0.0.0", port: int = 8080):
        """Run web monitor server."""
```

**Responsibilities:**
- Web-based monitoring interface
- Session status and statistics
- MCP call logging and display
- Health check endpoints

## Component Interactions

### 1. Tool Execution Flow
```
AI Assistant Request
  ↓
SimpleMCPServer.handle_request()
  ↓
MQTTTools.[tool_method]()
  ↓
MQTTConnectionManager.get_client()
  ↓
MessageCollector.collect_from_topic()
  ↓
MessagePruner.prune_messages()
  ↓
JSON Response to AI Assistant
```

### 2. Session Management Flow
```
establish_connection()
  ↓
MQTTConnectionManager.establish_connection()
  ↓
aiomqtt.Client() connection
  ↓
MQTTSession() creation
  ↓
Session UUID return
```

### 3. Message Collection Flow
```
subscribe_and_collect()
  ↓
MessageCollector.collect_from_topic()
  ↓ (async loop)
aiomqtt.Client.messages
  ↓ (stop conditions)
Time limit OR Message limit
  ↓
MessagePruner.prune_messages()
  ↓
Formatted response
```

## Error Handling Strategy

### 1. Connection Errors
- **MQTTConnectionError**: Broker unreachable, auth failed
- **SessionExpiredError**: Session TTL exceeded
- **ResourceLimitError**: Max connections reached

### 2. Runtime Errors  
- **TopicValidationError**: Invalid topic pattern
- **PayloadSizeError**: Message too large
- **QoSNotSupportedError**: Broker doesn't support QoS level

### 3. Recovery Mechanisms
- **Auto-reconnection**: Exponential backoff for connection loss
- **Graceful degradation**: Partial results on timeout
- **Resource cleanup**: Automatic session cleanup on errors

## Performance Considerations

### 1. Async Operations
- All MQTT operations use aiomqtt async client
- Non-blocking message collection
- Concurrent session management

### 2. Memory Management
- Hard limits on message collection
- Intelligent pruning for large datasets
- Session-based memory isolation

### 3. Resource Limits
- Maximum 5 concurrent MQTT connections
- Message collection time limits (10-300s)
- Topic discovery limits (1000 topics max) 