import logging
import json
from typing import Dict, List, Any, Optional
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from bson import ObjectId, json_util
import datetime

from connection_manager import ConnectionManager
from schema_analyzer import SchemaAnalyzer

logger = logging.getLogger(__name__)

class MongoDBTools:
    """MCP Tools for MongoDB operations."""
    
    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager
        self.schema_analyzer = SchemaAnalyzer()
    
    async def establish_connection(self, connection_string: str) -> Dict[str, Any]:
        """
        Establish a new MongoDB connection.
        
        Args:
            connection_string: MongoDB connection URI
            
        Returns:
            Connection result with session_id
        """
        try:
            session_id = await self.connection_manager.establish_connection(connection_string)
            
            # Get connection info
            conn_info = self.connection_manager.get_connection_info(session_id)
            
            return {
                'success': True,
                'session_id': session_id,
                'server_info': conn_info['server_info'] if conn_info else None,
                'host': conn_info['parsed_info']['hostname'] if conn_info else None,
                'message': f'Successfully connected to MongoDB server'
            }
            
        except Exception as e:
            logger.error(f"Failed to establish connection: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to connect to MongoDB'
            }
    
    def list_databases(self, session_id: str) -> Dict[str, Any]:
        """
        List all databases for a connection session.
        
        Args:
            session_id: Connection session ID
            
        Returns:
            List of databases with metadata
        """
        try:
            client = self.connection_manager.get_connection(session_id)
            if not client:
                return {
                    'success': False,
                    'error': 'Session not found or expired',
                    'databases': []
                }
            
            # Get database list
            db_list = client.list_database_names()
            
            # Get detailed info for each database
            databases = []
            for db_name in db_list:
                try:
                    db = client[db_name]
                    stats = db.command("dbStats")
                    
                    databases.append({
                        'name': db_name,
                        'size_mb': round(stats.get('dataSize', 0) / (1024 * 1024), 2),
                        'collection_count': stats.get('collections', 0),
                        'index_count': stats.get('indexes', 0),
                        'storage_size_mb': round(stats.get('storageSize', 0) / (1024 * 1024), 2)
                    })
                except:
                    # Fallback for databases without stats access
                    databases.append({
                        'name': db_name,
                        'size_mb': None,
                        'collection_count': None,
                        'index_count': None,
                        'storage_size_mb': None
                    })
            
            return {
                'success': True,
                'databases': databases,
                'total_count': len(databases)
            }
            
        except Exception as e:
            logger.error(f"Error listing databases for session {session_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'databases': []
            }
    
    def list_collections(self, session_id: str, database_name: str) -> Dict[str, Any]:
        """
        List all collections in a database.
        
        Args:
            session_id: Connection session ID
            database_name: Name of the database
            
        Returns:
            List of collections with metadata
        """
        try:
            client = self.connection_manager.get_connection(session_id)
            if not client:
                return {
                    'success': False,
                    'error': 'Session not found or expired',
                    'collections': []
                }
            
            db = client[database_name]
            collection_names = db.list_collection_names()
            
            collections = []
            for coll_name in collection_names:
                try:
                    collection = db[coll_name]
                    doc_count = collection.estimated_document_count()
                    
                    # Try to get more detailed stats
                    try:
                        stats = db.command("collStats", coll_name)
                        collections.append({
                            'name': coll_name,
                            'document_count': doc_count,
                            'size_mb': round(stats.get('size', 0) / (1024 * 1024), 2),
                            'avg_doc_size_bytes': stats.get('avgObjSize', 0),
                            'index_count': stats.get('nindexes', 0),
                            'storage_size_mb': round(stats.get('storageSize', 0) / (1024 * 1024), 2)
                        })
                    except:
                        collections.append({
                            'name': coll_name,
                            'document_count': doc_count,
                            'size_mb': None,
                            'avg_doc_size_bytes': None,
                            'index_count': None,
                            'storage_size_mb': None
                        })
                        
                except Exception as e:
                    logger.warning(f"Could not get stats for collection {coll_name}: {e}")
                    collections.append({
                        'name': coll_name,
                        'document_count': 0,
                        'error': str(e)
                    })
            
            return {
                'success': True,
                'database_name': database_name,
                'collections': collections,
                'total_count': len(collections)
            }
            
        except Exception as e:
            logger.error(f"Error listing collections for {database_name}: {e}")
            return {
                'success': False,
                'error': str(e),
                'collections': []
            }
    
    def get_collection_schema(self, session_id: str, database_name: str, collection_name: str) -> Dict[str, Any]:
        """
        Analyze and return the schema of a collection.
        
        Args:
            session_id: Connection session ID
            database_name: Name of the database
            collection_name: Name of the collection
            
        Returns:
            Schema analysis results
        """
        try:
            client = self.connection_manager.get_connection(session_id)
            if not client:
                return {
                    'success': False,
                    'error': 'Session not found or expired'
                }
            
            # Perform schema analysis
            schema_info = self.schema_analyzer.analyze_collection(
                client, database_name, collection_name
            )
            
            return {
                'success': True,
                'schema_analysis': schema_info
            }
            
        except Exception as e:
            logger.error(f"Error analyzing schema for {database_name}.{collection_name}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def query_collection(self, session_id: str, database_name: str, collection_name: str, 
                        query: Optional[Dict[str, Any]] = None, limit: int = 10,
                        projection: Optional[Dict[str, Any]] = None,
                        sort: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Query a collection with find operation.
        
        Args:
            session_id: Connection session ID
            database_name: Name of the database
            collection_name: Name of the collection
            query: MongoDB query filter (default: {})
            limit: Maximum number of documents to return
            projection: Fields to include/exclude
            sort: Sort specification
            
        Returns:
            Query results
        """
        try:
            client = self.connection_manager.get_connection(session_id)
            if not client:
                return {
                    'success': False,
                    'error': 'Session not found or expired',
                    'documents': []
                }
            
            db = client[database_name]
            collection = db[collection_name]
            
            # Default empty query
            if query is None:
                query = {}
            
            # Limit the result set for safety
            limit = min(limit, 100)  # Max 100 documents
            
            # Build the cursor
            cursor = collection.find(query, projection)
            
            if sort:
                cursor = cursor.sort(list(sort.items()))
            
            cursor = cursor.limit(limit)
            
            # Execute query and format results
            documents = []
            for doc in cursor:
                formatted_doc = self._format_document_for_output(doc)
                documents.append(formatted_doc)
            
            # Get total count for the query (limited for performance)
            try:
                if not query:  # Empty query
                    total_count = collection.estimated_document_count()
                else:
                    # For specific queries, use count_documents with a reasonable limit
                    total_count = collection.count_documents(query, limit=1000)
                    if total_count == 1000:
                        total_count = f"1000+"
            except:
                total_count = "unknown"
            
            return {
                'success': True,
                'database_name': database_name,
                'collection_name': collection_name,
                'query': query,
                'documents': documents,
                'returned_count': len(documents),
                'total_matching': total_count,
                'limit': limit
            }
            
        except Exception as e:
            logger.error(f"Error querying {database_name}.{collection_name}: {e}")
            return {
                'success': False,
                'error': str(e),
                'documents': []
            }
    
    def aggregate_collection(self, session_id: str, database_name: str, collection_name: str,
                           pipeline: List[Dict[str, Any]], limit: int = 10) -> Dict[str, Any]:
        """
        Run an aggregation pipeline on a collection.
        
        Args:
            session_id: Connection session ID
            database_name: Name of the database
            collection_name: Name of the collection
            pipeline: Aggregation pipeline stages
            limit: Maximum number of documents to return
            
        Returns:
            Aggregation results
        """
        try:
            client = self.connection_manager.get_connection(session_id)
            if not client:
                return {
                    'success': False,
                    'error': 'Session not found or expired',
                    'results': []
                }
            
            db = client[database_name]
            collection = db[collection_name]
            
            # Add a limit stage for safety
            pipeline_with_limit = pipeline.copy()
            pipeline_with_limit.append({"$limit": min(limit, 100)})
            
            # Execute aggregation
            results = []
            for doc in collection.aggregate(pipeline_with_limit):
                formatted_doc = self._format_document_for_output(doc)
                results.append(formatted_doc)
            
            return {
                'success': True,
                'database_name': database_name,
                'collection_name': collection_name,
                'pipeline': pipeline,
                'results': results,
                'result_count': len(results)
            }
            
        except Exception as e:
            logger.error(f"Error running aggregation on {database_name}.{collection_name}: {e}")
            return {
                'success': False,
                'error': str(e),
                'results': []
            }
    
    def get_sample_documents(self, session_id: str, database_name: str, collection_name: str,
                           limit: int = 5) -> Dict[str, Any]:
        """
        Get sample documents from a collection.
        
        Args:
            session_id: Connection session ID
            database_name: Name of the database
            collection_name: Name of the collection
            limit: Number of sample documents
            
        Returns:
            Sample documents
        """
        try:
            client = self.connection_manager.get_connection(session_id)
            if not client:
                return {
                    'success': False,
                    'error': 'Session not found or expired',
                    'documents': []
                }
            
            documents = self.schema_analyzer.get_sample_documents(
                client, database_name, collection_name, min(limit, 10)
            )
            
            return {
                'success': True,
                'database_name': database_name,
                'collection_name': collection_name,
                'documents': documents,
                'sample_size': len(documents)
            }
            
        except Exception as e:
            logger.error(f"Error getting sample documents: {e}")
            return {
                'success': False,
                'error': str(e),
                'documents': []
            }
    
    def get_connection_info(self, session_id: str) -> Dict[str, Any]:
        """Get information about a connection session."""
        conn_info = self.connection_manager.get_connection_info(session_id)
        if not conn_info:
            return {
                'success': False,
                'error': 'Session not found'
            }
        
        return {
            'success': True,
            'connection_info': conn_info
        }
    
    def list_active_connections(self) -> Dict[str, Any]:
        """List all active connections."""
        connections = self.connection_manager.list_active_connections()
        stats = self.connection_manager.get_stats()
        
        return {
            'success': True,
            'active_connections': connections,
            'stats': stats
        }
    
    async def close_connection(self, session_id: str) -> Dict[str, Any]:
        """Close a connection session."""
        success = await self.connection_manager.close_connection(session_id)
        
        return {
            'success': success,
            'message': 'Connection closed successfully' if success else 'Connection not found'
        }
    
    async def test_connection(self, session_id: str) -> Dict[str, Any]:
        """Test if a connection is still working."""
        result = await self.connection_manager.test_connectivity(session_id)
        return result
    
    def _format_document_for_output(self, doc: Any) -> Any:
        """Format document for JSON output, handling MongoDB-specific types."""
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