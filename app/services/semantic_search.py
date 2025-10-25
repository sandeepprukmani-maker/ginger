"""
Semantic Search Service for Task Library using PostgreSQL models
"""
import os
import json
import numpy as np
from typing import List, Dict, Optional
from app.models import db, LearnedTask
from app.services.vector_store import VectorStore, EmbeddingService


class SemanticSearchService:
    """High-level semantic search service for Task Library using PostgreSQL"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.vector_store = VectorStore(
            index_path='data/vector_index.faiss',
            metadata_path='data/vector_metadata.json'
        )
        self.embedding_service = EmbeddingService(api_key)
    
    def index_task(self, task: LearnedTask):
        """Index a LearnedTask for semantic search"""
        tags = json.loads(task.tags) if task.tags else []
        
        embedding = self.embedding_service.generate_task_embedding(
            task.task_name,
            task.description or '',
            tags
        )
        
        self.vector_store.add_vector(task.task_id, embedding)
        
        task.embedding_vector = embedding.tobytes()
        db.session.commit()
    
    def update_task_index(self, task: LearnedTask):
        """Update the index for an existing task"""
        tags = json.loads(task.tags) if task.tags else []
        
        embedding = self.embedding_service.generate_task_embedding(
            task.task_name,
            task.description or '',
            tags
        )
        
        self.vector_store.update_vector(task.task_id, embedding)
        
        task.embedding_vector = embedding.tobytes()
        db.session.commit()
    
    def search_tasks(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Search for tasks similar to the query.
        
        Returns:
            List of task dictionaries with similarity scores
        """
        query_embedding = self.embedding_service.generate_embedding(query)
        
        results = self.vector_store.search(query_embedding, top_k)
        
        tasks_with_scores = []
        for task_id, similarity_score in results:
            task = LearnedTask.query.filter_by(task_id=task_id).first()
            if task:
                task_dict = task.to_dict()
                task_dict['similarity_score'] = float(similarity_score)
                tasks_with_scores.append(task_dict)
        
        return tasks_with_scores
    
    def delete_task_from_index(self, task_id: str):
        """Remove a task from the search index"""
        self.vector_store.delete_vector(task_id)
    
    def reindex_all_tasks(self):
        """Rebuild the entire search index from scratch"""
        self.vector_store.clear()
        
        all_tasks = LearnedTask.query.order_by(LearnedTask.created_at.desc()).limit(10000).all()
        
        for task in all_tasks:
            try:
                self.index_task(task)
                print(f"Indexed task: {task.task_name}")
            except Exception as e:
                print(f"Failed to index task {task.task_id}: {e}")
