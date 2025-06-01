# bitsperity-mqtt-mcp - Business Logic

## Core Business Rules

### Connection Management
- **Connection Lifecycle**: Establish → Authenticate → Use → Monitor → Cleanup
- **Session Isolation**: Each connection gets a unique session ID (UUID)
- **Resource Limits**: Maximum 5 concurrent connections per MCP instance
- **Security**: No connection credentials stored beyond session lifetime
- **Auto-Cleanup**: Sessions expire after 1 hour of inactivity

### Message Collection Strategy
- **Temporal Boundaries**: All message collection is time-bounded (10-300 seconds)
- **Volume Limits**: Maximum 500 messages per collection to prevent memory issues
- **Stop Conditions**: Collection stops when EITHER time limit OR message limit reached
- **Quality over Quantity**: Intelligent pruning preserves diverse and important messages

### QoS Level Handling
- **QoS 0**: Fire and forget - no delivery guarantees
- **QoS 1**: At least once delivery - wait for PUBACK
- **QoS 2**: Exactly once delivery - full handshake (PUBREC/PUBREL/PUBCOMP)
- **Default**: QoS 0 for performance, QoS 1+ when delivery confirmation needed

### Topic Discovery Logic
- **Wildcard Strategy**: Use `#` for full discovery, `+` for single-level exploration
- **Time-based Discovery**: Listen for configurable period to capture topic activity
- **Deduplication**: Maintain unique topic list with last-seen timestamps
- **Memory Protection**: Hard limit of 1000 discovered topics

## Key Workflows

### 1. Connection Establishment Workflow
```
Input: MQTT connection string
├── Parse connection string (broker, port, auth, client_id)
├── Validate parameters (broker reachable, credentials valid)
├── Create MQTT client with clean session
├── Attempt connection with 30-second timeout
├── Generate unique session ID
├── Register session in connection manager
└── Return session_id or error
```

### 2. Message Collection Workflow
```
Input: session_id, topic_pattern, duration, max_messages
├── Validate session exists and is active
├── Subscribe to topic pattern with specified QoS
├── Start message collector with time/count limits
├── Collect messages with metadata (timestamp, topic, qos, payload)
├── Monitor stop conditions (duration OR max_messages)
├── Apply intelligent pruning if needed
├── Unsubscribe from topic
└── Return collected messages with statistics
```

### 3. Topic Discovery Workflow
```
Input: session_id, discovery_pattern, duration
├── Validate session exists and is active
├── Subscribe to wildcard pattern (default: #)
├── Collect unique topic names for specified duration
├── Track first-seen and last-seen timestamps per topic
├── Apply topic count limits (max 1000)
├── Unsubscribe from discovery pattern
└── Return topic list with metadata
```

### 4. Message Publishing Workflow
```
Input: session_id, topic, payload, qos, retain
├── Validate session exists and is active
├── Validate topic name and payload size
├── Publish message with specified QoS and retain flag
├── For QoS > 0: Wait for delivery confirmation
├── Track publish statistics (success/failure rates)
└── Return delivery confirmation or error
```

### 5. Device Debugging Workflow
```
Input: session_id, device_pattern, monitoring_duration
├── Validate session and parameters
├── Subscribe to device-specific topic pattern
├── Collect all messages matching device pattern
├── Analyze message patterns:
│   ├── Identify Last Will & Testament messages
│   ├── Detect heartbeat/status patterns
│   ├── Track connection state changes
│   └── Correlate messages across topics
├── Generate device health summary
└── Return debug report with device insights
```

## Data Processing Rules

### Intelligent Message Pruning Algorithm
```
When message count > target_size (default: 50):
1. Preserve ALL error/warning messages (priority 1)
2. Preserve first and last messages (temporal anchors)
3. Sample messages uniformly across time period
4. Prioritize messages with different payload structures
5. Include pruning summary explaining what was removed
```

### Payload Analysis Rules
- **JSON Detection**: Valid JSON → generate schema + field analysis
- **XML Detection**: Valid XML → basic structure analysis
- **Binary Detection**: Non-text data → mark as binary, analyze size only
- **Plain Text**: String data → content length and encoding analysis

### Topic Pattern Matching
- **Single Level Wildcard (+)**: Matches one topic level (sensor/+/temperature)
- **Multi Level Wildcard (#)**: Matches multiple levels (sensor/#)
- **Exact Match**: No wildcards, match specific topic name
- **Case Sensitivity**: MQTT topics are case-sensitive

### Performance Metrics Calculation
- **Throughput**: messages_received / collection_duration_seconds
- **Latency**: timestamp_received - timestamp_published (when available)
- **Message Rate**: moving average over collection period
- **Size Distribution**: min, max, mean, median of payload sizes

## Error Handling Rules

### Connection Errors
- **Broker Unreachable**: Return clear error with broker address
- **Authentication Failed**: Return auth error without exposing credentials
- **Timeout**: Return timeout error with attempted duration
- **Invalid Parameters**: Return validation error with specific issue

### Runtime Errors
- **Session Expired**: Return session error, require new connection
- **Topic Invalid**: Return topic validation error with MQTT spec reference
- **Payload Too Large**: Return size error with current limit
- **QoS Not Supported**: Return QoS error with broker capabilities

### Recovery Strategies
- **Connection Lost**: Attempt reconnection (3 retries with exponential backoff)
- **Subscription Failed**: Log error, continue with other subscriptions
- **Memory Pressure**: Trigger early pruning, reduce collection targets
- **Timeout Exceeded**: Graceful stop, return partial results

## Security & Privacy Rules

### Data Handling
- **No Persistence**: Message data never written to disk
- **Memory Only**: All data stored in RAM, cleared on session end
- **Credential Security**: Connection strings never logged or stored
- **Session Isolation**: Sessions cannot access each other's data

### Access Control
- **Session Validation**: All operations require valid session_id
- **Resource Limits**: Prevent resource exhaustion attacks
- **Input Validation**: Sanitize all user inputs
- **Error Information**: Error messages don't expose sensitive data

## Integration Rules

### MCP Protocol Compliance
- **JSON-RPC 2.0**: All communication follows JSON-RPC standard
- **Tool Definitions**: Each tool has complete JSON schema
- **Error Responses**: Standardized error format with codes
- **Request Validation**: Strict parameter validation per tool schema

### AI Assistant Optimization
- **Response Size**: Limit response size for AI processing
- **Human Readable**: Include summary information in results
- **Context Preservation**: Maintain enough context for AI understanding
- **Structured Output**: Use consistent data structures across tools 