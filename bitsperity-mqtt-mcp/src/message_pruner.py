"""
bitsperity-mqtt-mcp - Message Pruner
Phase 3: Simple Data Optimization

Simple but effective message pruning strategies (no AI needed)
Reduces large message collections (500) to manageable sizes (50)
while preserving important data.
"""

import logging
import json
import re
from typing import Dict, Any, List, Set, Optional
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


class SimpleMessagePruner:
    """
    Simple but effective message pruning strategies
    
    Reduces message collections using simple rules:
    1. Always preserve error/warning messages
    2. Keep first 10 and last 10 messages (temporal boundaries)
    3. Evenly distribute remaining messages over time
    4. Preserve unique message patterns
    5. Prefer smaller payloads for overview
    """
    
    def __init__(self, target_count: int = 50):
        """
        Initialize message pruner
        
        Args:
            target_count: Target number of messages to keep (default: 50)
        """
        self.target_count = target_count
        
        # Simple error detection patterns
        self.error_patterns = [
            r'error', r'fail', r'exception', r'critical', r'alert',
            r'warning', r'warn', r'problem', r'issue', r'fault',
            r'disconnected', r'timeout', r'rejected', r'denied'
        ]
        
        self.error_regex = re.compile('|'.join(self.error_patterns), re.IGNORECASE)
        
        logger.info(f"MessagePruner initialized with target_count={target_count}")
    
    def prune_messages(self, messages: List[Dict], target_count: Optional[int] = None) -> Dict[str, Any]:
        """
        Prune message collection using simple rules
        
        Args:
            messages: List of message dictionaries
            target_count: Override default target count
            
        Returns:
            Dict containing:
            - pruned_messages: Reduced message list
            - original_count: Original message count
            - pruned_count: Final message count
            - reduction_ratio: Percentage reduction
            - pruning_stats: Statistics about pruning strategy
        """
        start_time = datetime.now()
        target = target_count or self.target_count
        
        if not messages:
            return self._create_pruning_result([], [], start_time, "empty_input")
        
        if len(messages) <= target:
            return self._create_pruning_result(messages, messages, start_time, "no_pruning_needed")
        
        logger.info(f"Pruning {len(messages)} messages to {target} messages")
        
        # Step 1: Extract error/warning messages (always keep)
        error_messages = self._extract_error_messages(messages)
        non_error_messages = [msg for msg in messages if not self._is_error_message(msg)]
        
        # Step 2: Get temporal boundaries (first/last messages)
        boundary_count = min(10, len(non_error_messages) // 4)  # Adaptive boundary size
        first_messages = non_error_messages[:boundary_count]
        last_messages = non_error_messages[-boundary_count:] if len(non_error_messages) > boundary_count else []
        middle_messages = non_error_messages[boundary_count:-boundary_count] if len(non_error_messages) > 2 * boundary_count else []
        
        # Step 3: Calculate remaining slots
        used_slots = len(error_messages) + len(first_messages) + len(last_messages)
        remaining_slots = max(0, target - used_slots)
        
        # Step 4: Select distributed messages from middle
        distributed_messages = self._distribute_messages(middle_messages, remaining_slots)
        
        # Step 5: Combine all selected messages
        pruned_messages = self._combine_and_deduplicate([
            error_messages,
            first_messages, 
            distributed_messages,
            last_messages
        ])
        
        # Step 6: Final size enforcement
        if len(pruned_messages) > target:
            # Prefer errors and boundaries, cut from distributed
            keep_critical = error_messages + first_messages + last_messages
            remaining_target = target - len(keep_critical)
            if remaining_target > 0:
                pruned_messages = keep_critical + distributed_messages[:remaining_target]
            else:
                pruned_messages = keep_critical[:target]
        
        logger.info(f"Pruning complete: {len(messages)} → {len(pruned_messages)} messages")
        
        return self._create_pruning_result(messages, pruned_messages, start_time, "success")
    
    def _extract_error_messages(self, messages: List[Dict]) -> List[Dict]:
        """Extract messages that appear to be errors or warnings"""
        error_messages = []
        
        for msg in messages:
            if self._is_error_message(msg):
                error_messages.append(msg)
        
        logger.debug(f"Found {len(error_messages)} error/warning messages")
        return error_messages
    
    def _is_error_message(self, message: Dict) -> bool:
        """
        Simple error detection using pattern matching
        
        Checks topic and payload for error indicators
        """
        # Check topic for error patterns
        topic = message.get('topic', '').lower()
        if any(pattern in topic for pattern in ['error', 'warning', 'alarm', 'alert', 'fault']):
            return True
        
        # Check payload for error patterns
        payload = str(message.get('payload', '')).lower()
        if self.error_regex.search(payload):
            return True
        
        # Check for JSON error fields
        try:
            if isinstance(message.get('payload'), str):
                payload_data = json.loads(message['payload'])
                if isinstance(payload_data, dict):
                    # Check for common error fields
                    error_fields = ['error', 'warning', 'status', 'level', 'severity']
                    for field in error_fields:
                        if field in payload_data:
                            value = str(payload_data[field]).lower()
                            if any(pattern in value for pattern in ['error', 'warn', 'fail', 'critical']):
                                return True
        except (json.JSONDecodeError, TypeError):
            pass
        
        return False
    
    def _distribute_messages(self, messages: List[Dict], count: int) -> List[Dict]:
        """
        Distribute messages evenly over time/position
        
        Uses simple step-based distribution for even coverage
        """
        if not messages or count <= 0:
            return []
        
        if count >= len(messages):
            return messages
        
        # Simple step-based distribution
        step = len(messages) / count
        distributed = []
        
        for i in range(count):
            index = int(i * step)
            if index < len(messages):
                distributed.append(messages[index])
        
        # Add unique pattern preference (prefer different payload sizes/structures)
        if len(distributed) < count:
            # Add messages with unique characteristics
            seen_patterns = set()
            for msg in distributed:
                pattern = self._get_message_pattern(msg)
                seen_patterns.add(pattern)
            
            for msg in messages:
                if len(distributed) >= count:
                    break
                pattern = self._get_message_pattern(msg)
                if pattern not in seen_patterns and msg not in distributed:
                    distributed.append(msg)
                    seen_patterns.add(pattern)
        
        logger.debug(f"Distributed {len(distributed)} messages from {len(messages)}")
        return distributed
    
    def _get_message_pattern(self, message: Dict) -> str:
        """Get simple pattern signature for message"""
        topic = message.get('topic', '')
        payload = message.get('payload', '')
        
        # Simple pattern: topic structure + payload size category
        topic_parts = len(topic.split('/'))
        payload_size = len(str(payload))
        
        # Categorize payload size
        if payload_size < 50:
            size_category = 'small'
        elif payload_size < 200:
            size_category = 'medium'
        else:
            size_category = 'large'
        
        return f"{topic_parts}parts_{size_category}"
    
    def _combine_and_deduplicate(self, message_groups: List[List[Dict]]) -> List[Dict]:
        """
        Combine message groups and remove duplicates while preserving order
        """
        seen_messages = set()
        combined = []
        
        for group in message_groups:
            for msg in group:
                # Create simple message signature for deduplication
                signature = self._get_message_signature(msg)
                if signature not in seen_messages:
                    seen_messages.add(signature)
                    combined.append(msg)
        
        return combined
    
    def _get_message_signature(self, message: Dict) -> str:
        """Create simple signature for message deduplication"""
        topic = message.get('topic', '')
        payload = str(message.get('payload', ''))[:100]  # First 100 chars
        timestamp = message.get('timestamp', '')
        
        return f"{topic}:{hash(payload)}:{timestamp}"
    
    def _create_pruning_result(self, original_messages: List[Dict], pruned_messages: List[Dict], 
                              start_time: datetime, status: str) -> Dict[str, Any]:
        """Create standardized pruning result"""
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        original_count = len(original_messages)
        pruned_count = len(pruned_messages)
        
        reduction_ratio = (1 - pruned_count / original_count) * 100 if original_count > 0 else 0
        
        # Calculate pruning statistics
        error_count = len([msg for msg in pruned_messages if self._is_error_message(msg)])
        unique_topics = len(set(msg.get('topic', '') for msg in pruned_messages))
        
        return {
            'pruned_messages': pruned_messages,
            'original_count': original_count,
            'pruned_count': pruned_count,
            'reduction_ratio': round(reduction_ratio, 1),
            'processing_time_seconds': round(processing_time, 3),
            'status': status,
            'pruning_stats': {
                'error_messages_preserved': error_count,
                'unique_topics': unique_topics,
                'target_count': self.target_count,
                'strategy': 'simple_rules'
            },
            'timestamp': end_time.isoformat()
        }


class SchemaDetector:
    """
    Simple schema detection for MQTT messages
    
    Detects basic patterns in message structures without complex AI
    """
    
    def __init__(self):
        """Initialize schema detector"""
        self.topic_schemas = defaultdict(list)
        logger.info("SchemaDetector initialized")
    
    def analyze_messages(self, messages: List[Dict]) -> Dict[str, Any]:
        """
        Analyze message collection for basic schema patterns
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            Dict containing:
            - topic_schemas: Schema patterns by topic
            - payload_types: Distribution of payload types
            - common_fields: Common JSON fields found
            - schema_summary: High-level schema summary
        """
        start_time = datetime.now()
        
        if not messages:
            return self._create_schema_result({}, start_time, "empty_input")
        
        logger.info(f"Analyzing schema for {len(messages)} messages")
        
        # Group messages by topic pattern
        topic_patterns = defaultdict(list)
        payload_types = defaultdict(int)
        json_fields = defaultdict(int)
        
        for message in messages:
            topic = message.get('topic', '')
            payload = message.get('payload', '')
            
            # Generalize topic to pattern
            topic_pattern = self._generalize_topic(topic)
            topic_patterns[topic_pattern].append(message)
            
            # Detect payload type
            payload_type = self._detect_payload_type(payload)
            payload_types[payload_type] += 1
            
            # Extract JSON fields if applicable
            if payload_type == 'json':
                fields = self._extract_json_fields(payload)
                for field in fields:
                    json_fields[field] += 1
        
        # Analyze schema patterns per topic
        topic_schemas = {}
        for pattern, pattern_messages in topic_patterns.items():
            topic_schemas[pattern] = self._analyze_topic_schema(pattern_messages)
        
        # Create common fields summary
        common_fields = dict(sorted(json_fields.items(), key=lambda x: x[1], reverse=True)[:20])
        
        logger.info(f"Schema analysis complete: {len(topic_schemas)} topic patterns found")
        
        return self._create_schema_result({
            'topic_schemas': dict(topic_schemas),
            'payload_types': dict(payload_types),
            'common_fields': common_fields,
            'schema_summary': {
                'total_topics': len(topic_patterns),
                'total_messages': len(messages),
                'dominant_payload_type': max(payload_types.items(), key=lambda x: x[1])[0] if payload_types else 'unknown'
            }
        }, start_time, "success")
    
    def _generalize_topic(self, topic: str) -> str:
        """Generalize topic to pattern (replace variable parts with placeholders)"""
        if not topic:
            return "empty"
        
        parts = topic.split('/')
        generalized_parts = []
        
        for part in parts:
            # Simple heuristics for variable parts
            if (part.isdigit() or 
                len(part) > 10 or 
                any(char in part for char in ['_', '-']) and len(part) > 6):
                generalized_parts.append('+')  # Variable part
            else:
                generalized_parts.append(part)
        
        return '/'.join(generalized_parts)
    
    def _detect_payload_type(self, payload: Any) -> str:
        """Detect payload type using simple rules"""
        if not payload:
            return 'empty'
        
        payload_str = str(payload).strip()
        
        # JSON detection
        if payload_str.startswith(('{', '[')):
            try:
                json.loads(payload_str)
                return 'json'
            except json.JSONDecodeError:
                pass
        
        # Number detection
        try:
            float(payload_str)
            return 'number'
        except ValueError:
            pass
        
        # Binary detection (simple heuristic)
        if isinstance(payload, bytes) or 'binary data' in payload_str.lower():
            return 'binary'
        
        # Default to text
        return 'text'
    
    def _extract_json_fields(self, payload: Any) -> List[str]:
        """Extract field names from JSON payload"""
        try:
            data = json.loads(str(payload))
            if isinstance(data, dict):
                return list(data.keys())
        except (json.JSONDecodeError, TypeError):
            pass
        return []
    
    def _analyze_topic_schema(self, messages: List[Dict]) -> Dict[str, Any]:
        """Analyze schema for specific topic pattern"""
        if not messages:
            return {}
        
        payload_types = defaultdict(int)
        json_fields = defaultdict(int)
        sample_payloads = []
        
        for message in messages[:10]:  # Analyze first 10 messages
            payload = message.get('payload', '')
            payload_type = self._detect_payload_type(payload)
            payload_types[payload_type] += 1
            
            if payload_type == 'json':
                fields = self._extract_json_fields(payload)
                for field in fields:
                    json_fields[field] += 1
            
            # Keep sample payloads (limited size)
            if len(sample_payloads) < 3:
                sample_payload = str(payload)[:100]  # First 100 chars
                if sample_payload not in sample_payloads:
                    sample_payloads.append(sample_payload)
        
        return {
            'message_count': len(messages),
            'payload_types': dict(payload_types),
            'common_fields': dict(sorted(json_fields.items(), key=lambda x: x[1], reverse=True)[:10]),
            'sample_payloads': sample_payloads
        }
    
    def _create_schema_result(self, schema_data: Dict, start_time: datetime, status: str) -> Dict[str, Any]:
        """Create standardized schema analysis result"""
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        # Ensure all required fields are present
        default_result = {
            'topic_schemas': {},
            'payload_types': {},
            'common_fields': {},
            'schema_summary': {
                'total_topics': 0,
                'total_messages': 0,
                'dominant_payload_type': 'unknown'
            }
        }
        
        # Merge with provided schema_data
        result = {**default_result, **schema_data}
        
        return {
            **result,
            'processing_time_seconds': round(processing_time, 3),
            'status': status,
            'timestamp': end_time.isoformat(),
            'tool': 'schema_detector'
        } 