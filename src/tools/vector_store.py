"""
Vector Store - ChromaDB wrapper for semantic search and document retrieval.

This module provides persistent vector storage for the knowledge base,
enabling semantic search across retrieved documents.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class VectorStore:
    """
    Manage document embeddings and semantic search using ChromaDB.
    
    Features:
    - Persistent storage of document embeddings
    - Semantic similarity search
    - Metadata filtering
    - Batch operations
    """
    
    def __init__(
        self,
        persist_dir: str = "./chroma_db",
        collection_name: str = "knowledge_base",
        embedding_model: str = "all-MiniLM-L6-v2"
    ):
        """
        Initialize the vector store.
        
        Args:
            persist_dir: Directory for persistent storage
            collection_name: Name of the ChromaDB collection
            embedding_model: SentenceTransformer model for embeddings
        """
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(self.persist_dir),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}  # Use cosine similarity
        )
        
        # Initialize embedding model
        logger.info(f"Loading embedding model: {embedding_model}")
        self.encoder = SentenceTransformer(embedding_model)
        logger.info(f"Vector store initialized with {self.collection.count()} documents")
    
    def add_documents(
        self,
        texts: List[str],
        metadatas: List[Dict[str, Any]],
        ids: Optional[List[str]] = None
    ) -> None:
        """
        Add documents to the vector store.
        
        Args:
            texts: List of document texts
            metadatas: List of metadata dicts (must match length of texts)
            ids: Optional list of document IDs (auto-generated if None)
        """
        if len(texts) != len(metadatas):
            raise ValueError("texts and metadatas must have the same length")
        
        # Generate IDs if not provided
        if ids is None:
            import hashlib
            ids = [
                hashlib.md5(text.encode()).hexdigest()
                for text in texts
            ]
        
        logger.info(f"Adding {len(texts)} documents to vector store...")
        
        # Generate embeddings
        embeddings = self.encoder.encode(texts, show_progress_bar=True).tolist()
        
        # Add to ChromaDB
        self.collection.add(
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )
        
        logger.info(f"Successfully added {len(texts)} documents")
    
    def search(
        self,
        query: str,
        n_results: int = 10,
        where: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Semantic search for relevant documents.
        
        Args:
            query: Search query
            n_results: Number of results to return
            where: Optional metadata filter
        
        Returns:
            Dictionary with keys: ids, documents, metadatas, distances
        """
        logger.debug(f"Searching for: {query} (limit={n_results})")
        
        # Generate query embedding
        query_embedding = self.encoder.encode([query])[0].tolist()
        
        # Search ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where
        )
        
        # Flatten nested lists (ChromaDB returns lists of lists)
        flattened = {
            'ids': results['ids'][0] if results['ids'] else [],
            'documents': results['documents'][0] if results['documents'] else [],
            'metadatas': results['metadatas'][0] if results['metadatas'] else [],
            'distances': results['distances'][0] if results['distances'] else []
        }
        
        logger.debug(f"Found {len(flattened['ids'])} results")
        
        return flattened
    
    def get_by_id(self, ids: List[str]) -> Dict[str, Any]:
        """
        Retrieve documents by ID.
        
        Args:
            ids: List of document IDs
        
        Returns:
            Dictionary with documents and metadata
        """
        result = self.collection.get(ids=ids)
        return result
    
    def update_document(
        self,
        id: str,
        text: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Update a document's text or metadata.
        
        Args:
            id: Document ID
            text: New text (if updating)
            metadata: New metadata (if updating)
        """
        update_params = {'ids': [id]}
        
        if text is not None:
            embedding = self.encoder.encode([text])[0].tolist()
            update_params['embeddings'] = [embedding]
            update_params['documents'] = [text]
        
        if metadata is not None:
            update_params['metadatas'] = [metadata]
        
        self.collection.update(**update_params)
        logger.info(f"Updated document: {id}")
    
    def delete_documents(self, ids: List[str]) -> None:
        """
        Delete documents by ID.
        
        Args:
            ids: List of document IDs to delete
        """
        self.collection.delete(ids=ids)
        logger.info(f"Deleted {len(ids)} documents")
    
    def clear(self) -> None:
        """Clear all documents from the collection."""
        self.client.delete_collection(self.collection.name)
        self.collection = self.client.create_collection(
            name=self.collection.name,
            metadata={"hnsw:space": "cosine"}
        )
        logger.info("Vector store cleared")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get vector store statistics.
        
        Returns:
            Dictionary with statistics
        """
        return {
            'total_documents': self.collection.count(),
            'collection_name': self.collection.name,
            'persist_dir': str(self.persist_dir),
            'embedding_model': self.encoder.get_sentence_embedding_dimension()
        }
    
    def export_documents(self, output_file: str) -> None:
        """
        Export all documents to a JSON file.
        
        Args:
            output_file: Path to output JSON file
        """
        import json
        
        # Get all documents
        all_docs = self.collection.get()
        
        export_data = {
            'collection': self.collection.name,
            'count': len(all_docs['ids']),
            'documents': [
                {
                    'id': doc_id,
                    'text': doc,
                    'metadata': meta
                }
                for doc_id, doc, meta in zip(
                    all_docs['ids'],
                    all_docs['documents'],
                    all_docs['metadatas']
                )
            ]
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Exported {export_data['count']} documents to {output_file}")
    
    def __repr__(self) -> str:
        return f"VectorStore(collection={self.collection.name}, docs={self.collection.count()})"
