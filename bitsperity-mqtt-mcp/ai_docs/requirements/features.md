# bitsperity-mqtt-mcp - Feature Specifications

## F-001: MQTT Broker Connection
**Description**: Establishment and management of secure connections to MQTT brokers
**Priority**: Must-Have (MVP)

**Functional Requirements**:
- Accept connection string format: `mqtt://[username:password@]broker:port[/client_id]`
- Support Username/Password authentication
- Generate unique session IDs for connection tracking
- Validate broker connectivity before returning success
- Handle connection timeouts gracefully

**Business Rules**:
- Maximum 5 concurrent MQTT connections per MCP session
- Connection timeout: 30 seconds
- Session TTL: 1 hour (same as MongoDB MCP)
- Auto-reconnect on connection loss (3 retries)
- Clean session by default (no persistent subscriptions)

**Acceptance Criteria**:
- [ ] Connection string parsing works for all valid formats
- [ ] Authentication succeeds with valid credentials
- [ ] Connection fails gracefully with clear error messages
- [ ] Session ID is returned upon successful connection
- [ ] Connection can be tested independently

---

## F-002: Topic Discovery
**Description**: Discovery and listing of available MQTT topics using wildcards
**Priority**: Must-Have (MVP)

**Functional Requirements**:
- Subscribe to wildcard patterns (# and +)
- Collect topic names for specified duration (default 30s)
- Return unique topic list with last-seen timestamps
- Support multi-level wildcards for comprehensive discovery
- Limit discovery to prevent memory overflow

**Business Rules**:
- Discovery duration: 10-300 seconds (configurable)
- Maximum 1000 topics per discovery session
- Topic names must follow MQTT naming conventions
- Duplicate topics are deduplicated automatically

**Acceptance Criteria**:
- [ ] Wildcard `#` discovers all available topics
- [ ] Wildcard `+` discovers single-level topics
- [ ] Discovery stops after configured duration
- [ ] Topic list includes last-seen timestamps
- [ ] Memory usage stays within reasonable limits

---

## F-003: Message Collection & Monitoring
**Description**: Real-time collection and analysis of MQTT messages from topics
**Priority**: Must-Have (MVP)

**Functional Requirements**:
- Subscribe to specific topics or patterns
- Collect messages for configurable duration (10-300 seconds)
- Limit message count to prevent memory overflow (default 100)
- Support QoS levels 0, 1, and 2
- Automatic message pruning when limits exceeded

**Business Rules**:
- Default collection duration: 30 seconds
- Maximum messages per collection: 500
- Message payload size limit: 1MB per message
- Automatic stop when duration OR message limit reached
- Intelligent pruning favors recent and diverse messages

**Acceptance Criteria**:
- [ ] Messages collected in real-time from subscribed topics
- [ ] Collection stops at defined duration or message limit
- [ ] QoS levels are respected and acknowledged
- [ ] Large message collections are intelligently pruned
- [ ] Messages include timestamp, topic, QoS, and payload

---

## F-004: Message Publishing
**Description**: Publishing messages to MQTT topics with various QoS levels
**Priority**: Must-Have (MVP)

**Functional Requirements**:
- Publish to any valid MQTT topic
- Support text and binary payloads
- Configure QoS level (0, 1, 2)
- Set retain flag for persistent messages
- Return delivery confirmation for QoS > 0

**Business Rules**:
- Default QoS: 0 (fire and forget)
- Payload size limit: 1MB
- Topic names must follow MQTT naming conventions
- Retain flag is optional (default: false)
- Publish timeout: 30 seconds for QoS > 0

**Acceptance Criteria**:
- [ ] Messages are published to specified topics
- [ ] QoS levels are respected and confirmed
- [ ] Retain flag works correctly
- [ ] Large payloads are handled appropriately
- [ ] Delivery confirmations provided for QoS > 0

---

## F-005: Topic Schema Analysis
**Description**: Analysis of message structure and payload patterns for topics
**Priority**: Should-Have

**Functional Requirements**:
- Sample messages from topic for analysis period
- Detect JSON, XML, binary, and plain text formats
- Generate schema for JSON payloads
- Identify common fields and data types
- Report message format statistics

**Business Rules**:
- Minimum sample size: 10 messages
- Analysis duration: 30-300 seconds (configurable)
- Support for nested JSON structures
- Binary payloads marked as "binary" without analysis
- Schema confidence based on sample size

**Acceptance Criteria**:
- [ ] JSON payloads produce valid JSON schema
- [ ] Message format distribution is reported
- [ ] Common fields and types are identified
- [ ] Binary content is handled gracefully
- [ ] Schema confidence level is provided

---

## F-006: Device Debugging Support
**Description**: Specialized tools for debugging IoT device MQTT communication
**Priority**: Should-Have

**Functional Requirements**:
- Monitor device-specific topic patterns
- Detect Last Will & Testament messages
- Identify heartbeat and status patterns
- Correlate device messages across multiple topics
- Track device connection state changes

**Business Rules**:
- Device monitoring duration: 60-600 seconds
- Pattern matching supports MQTT wildcards
- LWT messages are flagged specially
- Connection state inferred from message patterns
- Maximum 10 devices monitored simultaneously

**Acceptance Criteria**:
- [ ] Device-specific messages are grouped correctly
- [ ] LWT messages are identified and flagged
- [ ] Connection state changes are detected
- [ ] Heartbeat patterns are recognized
- [ ] Cross-topic correlation works for device patterns

---

## F-007: Performance Monitoring
**Description**: Real-time monitoring of MQTT broker and topic performance metrics
**Priority**: Should-Have

**Functional Requirements**:
- Measure message throughput per topic
- Calculate message latency (publish to receive)
- Monitor message size distributions
- Detect traffic spikes and patterns
- Generate performance summary reports

**Business Rules**:
- Metrics collection period: 60-1800 seconds
- Latency measured in milliseconds
- Throughput calculated as messages/second
- Size distribution in bytes
- Performance data not persisted beyond session

**Acceptance Criteria**:
- [ ] Throughput metrics are accurate
- [ ] Latency measurements work for different QoS levels
- [ ] Message size statistics are generated
- [ ] Traffic patterns are identified
- [ ] Performance summary is human-readable

---

## F-008: Integration Testing Tools
**Description**: Automated testing capabilities for MQTT integrations
**Priority**: Could-Have

**Functional Requirements**:
- Send test message and monitor for response
- Measure round-trip time for request-response patterns
- Compare expected vs actual message formats
- Validate message delivery across QoS levels
- Generate integration test reports

**Business Rules**:
- Test timeout: 60 seconds
- Response correlation via message content or timing
- Format validation supports JSON Schema
- Test results include success/failure status
- Multiple test scenarios can run sequentially

**Acceptance Criteria**:
- [ ] Test messages trigger expected responses
- [ ] Round-trip times are measured accurately
- [ ] Message format validation works correctly
- [ ] QoS delivery is verified
- [ ] Test results are clearly reported

---

## F-009: Intelligent Message Pruning
**Description**: Smart reduction of large message collections for AI assistant processing
**Priority**: Must-Have (MVP)

**Functional Requirements**:
- Automatically reduce message collections when they exceed target size
- Preserve message diversity (different payloads, topics, timestamps)
- Prioritize error messages and warnings
- Maintain temporal distribution across collection period
- Include pruning summary in results

**Business Rules**:
- Target size for AI processing: 50 messages
- Error/warning messages always preserved
- Temporal sampling ensures time distribution
- Payload diversity prioritized over volume
- Pruning algorithm is deterministic

**Acceptance Criteria**:
- [ ] Large collections are reduced to target size
- [ ] Important messages (errors) are preserved
- [ ] Time distribution is maintained after pruning
- [ ] Message diversity is maximized
- [ ] Pruning summary explains what was removed

---

## F-010: Session Management
**Description**: Secure management of MQTT connection sessions
**Priority**: Must-Have (MVP)

**Functional Requirements**:
- Create unique session IDs for each connection
- Track session expiration times
- Clean up resources on session end
- List all active sessions
- Force-close sessions if needed

**Business Rules**:
- Session TTL: 3600 seconds (1 hour)
- Maximum 10 sessions per MCP instance
- Sessions auto-expire after inactivity
- Cleanup includes MQTT disconnection
- Session IDs are UUIDs

**Acceptance Criteria**:
- [ ] Sessions are created with unique IDs
- [ ] Sessions expire automatically after TTL
- [ ] Resource cleanup happens on session end
- [ ] Active sessions can be listed
- [ ] Sessions can be manually closed 