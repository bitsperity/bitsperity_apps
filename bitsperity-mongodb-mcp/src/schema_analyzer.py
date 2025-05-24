import logging
from typing import Dict, List, Any, Optional, Set
from collections import defaultdict, Counter
import pymongo
from pymongo import MongoClient
from bson import ObjectId
import datetime

logger = logging.getLogger(__name__)

class SchemaAnalyzer:
    """Analyzes MongoDB collection schemas and provides insights."""
    
    def __init__(self, sample_size: int = 100, max_depth: int = 3):
        self.sample_size = sample_size
        self.max_depth = max_depth
    
    def analyze_collection(self, client: MongoClient, db_name: str, collection_name: str) -> Dict[str, Any]:
        """
        Analyze a MongoDB collection and return comprehensive schema information.
        
        Args:
            client: MongoDB client
            db_name: Database name
            collection_name: Collection name
            
        Returns:
            Schema analysis results
        """
        try:
            db = client[db_name]
            collection = db[collection_name]
            
            # Get collection stats
            stats = self._get_collection_stats(collection)
            
            # Get sample documents
            sample_docs = self._get_sample_documents(collection)
            
            # Analyze schema
            schema = self._infer_schema(sample_docs)
            
            # Get field statistics
            field_stats = self._get_field_statistics(sample_docs)
            
            # Get indexes
            indexes = self._get_index_info(collection)
            
            return {
                'collection_name': collection_name,
                'database_name': db_name,
                'stats': stats,
                'schema': schema,
                'field_statistics': field_stats,
                'indexes': indexes,
                'sample_size': len(sample_docs),
                'analysis_timestamp': datetime.datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing collection {db_name}.{collection_name}: {e}")
            raise
    
    def _get_collection_stats(self, collection) -> Dict[str, Any]:
        """Get basic collection statistics."""
        try:
            stats = collection.estimated_document_count()
            # Try to get more detailed stats if available
            try:
                detailed_stats = collection.database.command("collStats", collection.name)
                return {
                    'document_count': stats,
                    'size_bytes': detailed_stats.get('size', 0),
                    'storage_size': detailed_stats.get('storageSize', 0),
                    'avg_doc_size': detailed_stats.get('avgObjSize', 0),
                    'index_count': detailed_stats.get('nindexes', 0),
                    'total_index_size': detailed_stats.get('totalIndexSize', 0)
                }
            except:
                return {
                    'document_count': stats,
                    'size_bytes': None,
                    'storage_size': None,
                    'avg_doc_size': None,
                    'index_count': None,
                    'total_index_size': None
                }
        except Exception as e:
            logger.warning(f"Could not get collection stats: {e}")
            return {
                'document_count': 0,
                'error': str(e)
            }
    
    def _get_sample_documents(self, collection) -> List[Dict[str, Any]]:
        """Get a representative sample of documents from the collection."""
        try:
            # Use aggregation with $sample for better randomness
            pipeline = [{"$sample": {"size": self.sample_size}}]
            sample_docs = list(collection.aggregate(pipeline))
            
            # If collection is smaller than sample size, get all documents
            if len(sample_docs) < self.sample_size:
                total_count = collection.estimated_document_count()
                if total_count < self.sample_size:
                    sample_docs = list(collection.find().limit(self.sample_size))
            
            return sample_docs
            
        except Exception as e:
            logger.warning(f"Could not get sample documents: {e}")
            # Fallback to simple find
            try:
                return list(collection.find().limit(self.sample_size))
            except:
                return []
    
    def _infer_schema(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Infer schema from sample documents."""
        if not documents:
            return {}
        
        schema = {}
        
        for doc in documents:
            self._analyze_document(doc, schema, 0)
        
        # Convert to readable format
        return self._format_schema(schema, len(documents))
    
    def _analyze_document(self, doc: Any, schema: Dict[str, Any], depth: int):
        """Recursively analyze a document structure."""
        if depth > self.max_depth:
            return
        
        if isinstance(doc, dict):
            for key, value in doc.items():
                if key not in schema:
                    schema[key] = {
                        'types': defaultdict(int),
                        'count': 0,
                        'examples': [],
                        'nested': {}
                    }
                
                schema[key]['count'] += 1
                value_type = self._get_value_type(value)
                schema[key]['types'][value_type] += 1
                
                # Store examples (limit to 3)
                if len(schema[key]['examples']) < 3:
                    if not self._is_sensitive_field(key):
                        example_value = self._format_example_value(value)
                        if example_value not in schema[key]['examples']:
                            schema[key]['examples'].append(example_value)
                
                # Recursively analyze nested structures
                if isinstance(value, dict) and depth < self.max_depth:
                    self._analyze_document(value, schema[key]['nested'], depth + 1)
                elif isinstance(value, list) and value and depth < self.max_depth:
                    # Analyze first few items in array
                    for item in value[:3]:
                        self._analyze_document(item, schema[key]['nested'], depth + 1)
    
    def _get_value_type(self, value: Any) -> str:
        """Get human-readable type for a value."""
        if value is None:
            return 'null'
        elif isinstance(value, bool):
            return 'boolean'
        elif isinstance(value, int):
            return 'integer'
        elif isinstance(value, float):
            return 'number'
        elif isinstance(value, str):
            return 'string'
        elif isinstance(value, ObjectId):
            return 'ObjectId'
        elif isinstance(value, datetime.datetime):
            return 'date'
        elif isinstance(value, list):
            return 'array'
        elif isinstance(value, dict):
            return 'object'
        else:
            return type(value).__name__
    
    def _format_example_value(self, value: Any) -> Any:
        """Format a value for use as an example."""
        if isinstance(value, ObjectId):
            return str(value)
        elif isinstance(value, datetime.datetime):
            return value.isoformat()
        elif isinstance(value, (list, dict)):
            return str(value)[:100] + "..." if len(str(value)) > 100 else str(value)
        else:
            return value
    
    def _is_sensitive_field(self, field_name: str) -> bool:
        """Check if a field might contain sensitive information."""
        sensitive_keywords = [
            'password', 'pass', 'pwd', 'secret', 'token', 'key', 'api_key',
            'private', 'confidential', 'ssn', 'social', 'credit', 'card',
            'email', 'phone', 'address'
        ]
        field_lower = field_name.lower()
        return any(keyword in field_lower for keyword in sensitive_keywords)
    
    def _format_schema(self, schema: Dict[str, Any], total_docs: int) -> Dict[str, Any]:
        """Format schema for output."""
        formatted = {}
        
        for field_name, field_info in schema.items():
            # Calculate field statistics
            occurrence_rate = field_info['count'] / total_docs if total_docs > 0 else 0
            is_required = occurrence_rate > 0.9  # Field appears in >90% of documents
            
            # Get primary type (most common)
            primary_type = max(field_info['types'].items(), key=lambda x: x[1])[0] if field_info['types'] else 'unknown'
            
            # Type distribution
            type_distribution = dict(field_info['types'])
            
            formatted[field_name] = {
                'type': primary_type,
                'required': is_required,
                'occurrence_rate': round(occurrence_rate, 3),
                'type_distribution': type_distribution,
                'examples': field_info['examples'][:3],  # Limit to 3 examples
            }
            
            # Add nested schema if exists
            if field_info['nested']:
                formatted[field_name]['nested_schema'] = self._format_schema(
                    field_info['nested'], field_info['count']
                )
        
        return formatted
    
    def _get_field_statistics(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get statistics about fields across all documents."""
        if not documents:
            return {}
        
        all_fields = set()
        field_counts = Counter()
        
        for doc in documents:
            doc_fields = self._get_all_field_paths(doc)
            all_fields.update(doc_fields)
            field_counts.update(doc_fields)
        
        total_docs = len(documents)
        
        return {
            'total_unique_fields': len(all_fields),
            'total_documents_analyzed': total_docs,
            'field_frequency': {
                field: {
                    'count': count,
                    'percentage': round((count / total_docs) * 100, 2)
                }
                for field, count in field_counts.most_common()
            }
        }
    
    def _get_all_field_paths(self, doc: Any, prefix: str = '') -> Set[str]:
        """Get all field paths from a document (including nested)."""
        fields = set()
        
        if isinstance(doc, dict):
            for key, value in doc.items():
                field_path = f"{prefix}.{key}" if prefix else key
                fields.add(field_path)
                
                if isinstance(value, dict):
                    fields.update(self._get_all_field_paths(value, field_path))
                elif isinstance(value, list) and value and isinstance(value[0], dict):
                    # Analyze first item in array for nested structure
                    fields.update(self._get_all_field_paths(value[0], field_path))
        
        return fields
    
    def _get_index_info(self, collection) -> List[Dict[str, Any]]:
        """Get information about collection indexes."""
        try:
            indexes = []
            for index_info in collection.list_indexes():
                index_data = {
                    'name': index_info.get('name'),
                    'keys': dict(index_info.get('key', {})),
                    'unique': index_info.get('unique', False),
                    'sparse': index_info.get('sparse', False),
                    'background': index_info.get('background', False)
                }
                
                # Add size information if available
                if 'textIndexVersion' in index_info:
                    index_data['type'] = 'text'
                elif any(v == '2dsphere' for v in index_data['keys'].values()):
                    index_data['type'] = 'geospatial'
                else:
                    index_data['type'] = 'standard'
                
                indexes.append(index_data)
            
            return indexes
            
        except Exception as e:
            logger.warning(f"Could not get index information: {e}")
            return []
    
    def get_sample_documents(self, client: MongoClient, db_name: str, collection_name: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get a few sample documents for preview."""
        try:
            db = client[db_name]
            collection = db[collection_name]
            
            # Get sample documents
            docs = list(collection.find().limit(limit))
            
            # Format ObjectIds and dates for JSON serialization
            formatted_docs = []
            for doc in docs:
                formatted_doc = self._format_document_for_output(doc)
                formatted_docs.append(formatted_doc)
            
            return formatted_docs
            
        except Exception as e:
            logger.error(f"Error getting sample documents: {e}")
            return []
    
    def _format_document_for_output(self, doc: Any) -> Any:
        """Format document for JSON output."""
        if isinstance(doc, dict):
            formatted = {}
            for key, value in doc.items():
                formatted[key] = self._format_document_for_output(value)
            return formatted
        elif isinstance(doc, list):
            return [self._format_document_for_output(item) for item in doc]
        elif isinstance(doc, ObjectId):
            return str(doc)
        elif isinstance(doc, datetime.datetime):
            return doc.isoformat()
        else:
            return doc 