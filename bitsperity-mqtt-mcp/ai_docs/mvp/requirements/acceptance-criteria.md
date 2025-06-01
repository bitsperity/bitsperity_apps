# bitsperity-mqtt-mcp - Acceptance Criteria

## MVP Feature Acceptance Criteria

### AC-001: MQTT Broker Connection (F-001)

#### AC-001.1: Connection String Parsing
**Given** a valid MQTT connection string  
**When** the establish_connection tool is called  
**Then** the connection string is parsed correctly

- [ ] `mqtt://broker.local:1883` → broker=broker.local, port=1883, no auth
- [ ] `mqtt://user:pass@broker:1883` → broker=broker, port=1883, auth=user:pass
- [ ] `mqtt://user:pass@broker:1883/client123` → includes client_id=client123
- [ ] Invalid formats return clear parsing error messages

#### AC-001.2: Connection Establishment
**Given** a parsed connection string  
**When** connection is attempted  
**Then** connection succeeds or fails gracefully

- [ ] Successful connection returns unique session_id (UUID format)
- [ ] Connection timeout after 30 seconds returns timeout error
- [ ] Invalid credentials return authentication error
- [ ] Unreachable broker returns connection error with broker details

#### AC-001.3: Session Management
**Given** a successful connection  
**When** session is created  
**Then** session is properly managed

- [ ] Session ID is unique across all connections
- [ ] Session appears in list_active_connections
- [ ] Session expires after 1 hour of inactivity
- [ ] Maximum 5 concurrent sessions enforced

---

### AC-002: Topic Discovery (F-002)

#### AC-002.1: Wildcard Discovery
**Given** an active MQTT session  
**When** list_topics is called with wildcard patterns  
**Then** topics are discovered correctly

- [ ] Pattern `#` discovers all available topics
- [ ] Pattern `+` discovers single-level topics only
- [ ] Pattern `sensor/+/temperature` discovers matching topics
- [ ] Discovery runs for specified duration (default 30s)

#### AC-002.2: Topic Collection
**Given** topic discovery is running  
**When** messages are received on various topics  
**Then** topic list is built correctly

- [ ] Duplicate topics are deduplicated
- [ ] Each topic includes last-seen timestamp
- [ ] Maximum 1000 topics enforced
- [ ] Topic list sorted alphabetically

#### AC-002.3: Discovery Results
**Given** topic discovery completion  
**When** results are returned  
**Then** topic data is complete and accurate

- [ ] Result includes total discovery duration
- [ ] Result includes count of unique topics found
- [ ] Each topic has name and last_seen timestamp
- [ ] Empty result when no topics found (with explanation)

---

### AC-003: Message Collection & Monitoring (F-003)

#### AC-003.1: Message Subscription
**Given** an active MQTT session  
**When** subscribe_and_collect is called  
**Then** subscription works correctly

- [ ] Subscribes to exact topic names
- [ ] Subscribes to wildcard patterns
- [ ] QoS level is respected (0, 1, or 2)
- [ ] Subscription confirmed before collection starts

#### AC-003.2: Message Collection
**Given** an active subscription  
**When** messages are received  
**Then** messages are collected properly

- [ ] Messages collected for specified duration
- [ ] Collection stops at max_messages limit
- [ ] Each message includes: timestamp, topic, qos, payload
- [ ] Message order preserved (chronological)

#### AC-003.3: Collection Limits
**Given** message collection in progress  
**When** limits are reached  
**Then** collection stops appropriately

- [ ] Stops after specified duration (10-300 seconds)
- [ ] Stops after max_messages reached (default 100)
- [ ] Triggers intelligent pruning when >500 messages
- [ ] Unsubscribes from topic after collection

#### AC-003.4: Message Metadata
**Given** collected messages  
**When** results are returned  
**Then** metadata is complete and accurate

- [ ] Timestamp in ISO format with timezone
- [ ] Topic name exactly as received
- [ ] QoS level as integer (0, 1, or 2)
- [ ] Payload as string or base64 for binary data
- [ ] Message size in bytes included

---

### AC-004: Message Publishing (F-004)

#### AC-004.1: Basic Publishing
**Given** an active MQTT session  
**When** publish_message is called  
**Then** message is published correctly

- [ ] Message sent to specified topic
- [ ] Payload transmitted exactly as provided
- [ ] QoS level respected (0, 1, or 2)
- [ ] Retain flag applied correctly

#### AC-004.2: QoS Acknowledgments
**Given** publishing with QoS > 0  
**When** message is sent  
**Then** delivery confirmation is received

- [ ] QoS 1: PUBACK received within timeout
- [ ] QoS 2: Full handshake completed (PUBREC/PUBREL/PUBCOMP)
- [ ] Timeout after 30 seconds returns error
- [ ] Delivery confirmation included in response

#### AC-004.3: Payload Handling
**Given** various payload types  
**When** publishing messages  
**Then** payloads are handled correctly

- [ ] Text payloads sent as UTF-8 strings
- [ ] JSON payloads preserved exactly
- [ ] Binary data handled appropriately
- [ ] Payload size limit (1MB) enforced

#### AC-004.4: Error Handling
**Given** invalid publish parameters  
**When** publish_message is called  
**Then** appropriate errors are returned

- [ ] Invalid topic names rejected with clear error
- [ ] Oversized payloads rejected with size error
- [ ] Invalid QoS values rejected
- [ ] Session validation errors returned

---

### AC-005: Intelligent Message Pruning (F-009)

#### AC-005.1: Pruning Trigger
**Given** message collection exceeding target size  
**When** pruning is triggered  
**Then** collection is reduced appropriately

- [ ] Pruning triggered when >50 messages (default target)
- [ ] Pruning reduces to exactly target size
- [ ] Pruning algorithm is deterministic
- [ ] Pruning summary included in results

#### AC-005.2: Message Preservation
**Given** pruning is active  
**When** selecting messages to keep  
**Then** important messages are preserved

- [ ] ALL error/warning messages preserved (priority 1)
- [ ] First and last messages preserved (temporal anchors)
- [ ] Messages sampled uniformly across time period
- [ ] Diverse payload structures prioritized

#### AC-005.3: Pruning Summary
**Given** pruning completion  
**When** results are returned  
**Then** pruning information is provided

- [ ] Original message count reported
- [ ] Final message count reported
- [ ] Pruning strategy explanation included
- [ ] Preserved message categories listed

---

### AC-006: Session Management (F-010)

#### AC-006.1: Session Creation
**Given** connection establishment  
**When** session is created  
**Then** session is properly initialized

- [ ] Session ID generated as UUID
- [ ] Session registered with current timestamp
- [ ] Session includes connection metadata
- [ ] Session limits enforced (max 10 sessions)

#### AC-006.2: Session Listing
**Given** active sessions exist  
**When** list_active_connections is called  
**Then** session list is accurate

- [ ] All active sessions included
- [ ] Session info includes: id, broker, created_at, last_used
- [ ] Expired sessions excluded from list
- [ ] Empty list when no active sessions

#### AC-006.3: Session Expiration
**Given** session inactivity  
**When** TTL expires (1 hour)  
**Then** session is cleaned up

- [ ] Session automatically expires after 3600 seconds
- [ ] MQTT connection properly closed
- [ ] Session removed from active list
- [ ] Resources cleaned up (memory freed)

#### AC-006.4: Manual Session Closure
**Given** an active session  
**When** close_connection is called  
**Then** session is properly terminated

- [ ] MQTT connection gracefully closed
- [ ] Session immediately removed from active list
- [ ] All associated resources cleaned up
- [ ] Success confirmation returned

---

## Integration Acceptance Criteria

### AC-I01: MCP Protocol Compliance
**Given** any MCP tool call  
**When** communication occurs  
**Then** MCP protocol is followed correctly

- [ ] All requests/responses follow JSON-RPC 2.0 format
- [ ] Tool schemas match actual parameter handling
- [ ] Error responses include proper error codes
- [ ] Request validation follows tool schemas exactly

### AC-I02: AI Assistant Optimization
**Given** tool responses  
**When** data is returned to AI assistant  
**Then** responses are optimized for AI processing

- [ ] Response size suitable for LLM context limits
- [ ] Data structures consistent across tools
- [ ] Human-readable summaries included
- [ ] Context preserved for follow-up questions

### AC-I03: Error Handling Consistency
**Given** any error condition  
**When** errors occur  
**Then** error handling is consistent

- [ ] Error messages are clear and actionable
- [ ] Sensitive information not exposed in errors
- [ ] Error categories standardized across tools
- [ ] Recovery suggestions provided where applicable

### AC-I04: Performance Requirements
**Given** normal operation  
**When** tools are executed  
**Then** performance requirements are met

- [ ] Connection establishment <30 seconds
- [ ] Message collection starts within 2 seconds
- [ ] Topic discovery completes within configured time
- [ ] Memory usage stays within reasonable limits

---

## Quality Gates

### Functional Quality Gates
- [ ] All MVP features (F-001, F-002, F-003, F-004, F-009, F-010) pass acceptance criteria
- [ ] All MCP tools execute without errors in happy path scenarios
- [ ] Error handling works correctly for all identified error conditions
- [ ] Session management operates reliably under normal load

### Performance Quality Gates
- [ ] Connection establishment completes within 30 seconds
- [ ] Message collection handles 100 messages/second throughput
- [ ] Memory usage remains stable during extended operation
- [ ] No memory leaks during session lifecycle

### Security Quality Gates
- [ ] No credentials stored persistently
- [ ] Session isolation maintained between connections
- [ ] Input validation prevents injection attacks
- [ ] Error messages don't leak sensitive information

### Integration Quality Gates
- [ ] MCP protocol compliance verified with actual AI assistants
- [ ] Tool responses processable by LLM within context limits
- [ ] SSH integration works with Umbrel deployment model
- [ ] Web monitoring interface accessible and functional 