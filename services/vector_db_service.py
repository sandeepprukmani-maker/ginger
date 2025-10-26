import os
import logging
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from typing import List, Dict, Any
import hashlib

logger = logging.getLogger(__name__)

class VectorDBService:
    def __init__(self):
        self.persist_directory = "./chroma_db"
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        api_key = os.environ.get('OPENAI_API_KEY')
        if api_key:
            self.embedding_function = embedding_functions.OpenAIEmbeddingFunction(
                api_key=api_key,
                model_name="text-embedding-3-small"
            )
            logger.info("Using OpenAI embeddings for vector database")
        else:
            logger.warning("OPENAI_API_KEY not found, AMA feature will not work until API key is configured")
            self.embedding_function = None
        
        self.project_collection = self._get_or_create_collection("project_knowledge")
        self.conversation_collection = self._get_or_create_collection("conversation_memory")
        self.feedback_collection = self._get_or_create_collection("validated_knowledge")
        
    def _get_or_create_collection(self, name: str):
        try:
            collection_kwargs = {
                "name": name,
                "metadata": {"hnsw:space": "cosine"}
            }
            if self.embedding_function:
                collection_kwargs["embedding_function"] = self.embedding_function
            
            return self.client.get_or_create_collection(**collection_kwargs)
        except Exception as e:
            logger.error(f"Error creating collection {name}: {str(e)}")
            raise
    
    def _generate_id(self, text: str, source: str = "") -> str:
        content = f"{source}:{text}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def add_project_knowledge(self, documents: List[Dict[str, Any]]):
        try:
            ids = []
            texts = []
            metadatas = []
            
            for doc in documents:
                doc_id = self._generate_id(doc['text'], doc.get('source', 'unknown'))
                ids.append(doc_id)
                texts.append(doc['text'])
                metadatas.append({
                    'source': doc.get('source', 'unknown'),
                    'source_type': doc.get('source_type', 'document'),
                    'timestamp': doc.get('timestamp', ''),
                    'title': doc.get('title', ''),
                    'url': doc.get('url', '')
                })
            
            if ids:
                self.project_collection.add(
                    ids=ids,
                    documents=texts,
                    metadatas=metadatas
                )
                logger.info(f"Added {len(ids)} documents to project knowledge")
        except Exception as e:
            logger.error(f"Error adding project knowledge: {str(e)}")
            raise
    
    def add_conversation(self, question: str, answer: str, context: str = ""):
        try:
            conv_id = self._generate_id(f"{question}:{answer}", "conversation")
            self.conversation_collection.add(
                ids=[conv_id],
                documents=[f"Q: {question}\nA: {answer}"],
                metadatas=[{
                    'question': question,
                    'answer': answer,
                    'context': context,
                    'timestamp': str(os.times().elapsed)
                }]
            )
            logger.debug(f"Added conversation to memory: {conv_id}")
        except Exception as e:
            logger.error(f"Error adding conversation: {str(e)}")
    
    def add_validated_knowledge(self, question: str, validated_answer: str, metadata: Dict[str, Any] = None):
        try:
            validated_id = self._generate_id(f"{question}:{validated_answer}", "validated")
            meta = metadata or {}
            meta.update({
                'question': question,
                'answer': validated_answer,
                'validated': True,
                'timestamp': str(os.times().elapsed)
            })
            
            self.feedback_collection.add(
                ids=[validated_id],
                documents=[f"Q: {question}\nValidated A: {validated_answer}"],
                metadatas=[meta]
            )
            logger.info(f"Added validated knowledge: {validated_id}")
        except Exception as e:
            logger.error(f"Error adding validated knowledge: {str(e)}")
    
    def search_project_knowledge(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        try:
            results = self.project_collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            formatted_results = []
            if results and results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    formatted_results.append({
                        'text': doc,
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'distance': results['distances'][0][i] if results.get('distances') else 0
                    })
            
            return formatted_results
        except Exception as e:
            logger.error(f"Error searching project knowledge: {str(e)}")
            return []
    
    def search_conversation_memory(self, query: str, n_results: int = 3) -> List[Dict[str, Any]]:
        try:
            results = self.conversation_collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            formatted_results = []
            if results and results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    formatted_results.append({
                        'text': doc,
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'distance': results['distances'][0][i] if results.get('distances') else 0
                    })
            
            return formatted_results
        except Exception as e:
            logger.error(f"Error searching conversation memory: {str(e)}")
            return []
    
    def search_validated_knowledge(self, query: str, n_results: int = 3) -> List[Dict[str, Any]]:
        try:
            results = self.feedback_collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            formatted_results = []
            if results and results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    formatted_results.append({
                        'text': doc,
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'distance': results['distances'][0][i] if results.get('distances') else 0
                    })
            
            return formatted_results
        except Exception as e:
            logger.error(f"Error searching validated knowledge: {str(e)}")
            return []
    
    def get_collection_stats(self) -> Dict[str, int]:
        try:
            return {
                'project_knowledge_count': self.project_collection.count(),
                'conversation_count': self.conversation_collection.count(),
                'validated_knowledge_count': self.feedback_collection.count()
            }
        except Exception as e:
            logger.error(f"Error getting stats: {str(e)}")
            return {}
    
    def reset_all(self):
        try:
            self.client.reset()
            self.project_collection = self._get_or_create_collection("project_knowledge")
            self.conversation_collection = self._get_or_create_collection("conversation_memory")
            self.feedback_collection = self._get_or_create_collection("validated_knowledge")
            logger.info("All collections reset")
        except Exception as e:
            logger.error(f"Error resetting collections: {str(e)}")
