#!/usr/bin/env python3
"""Re-index all learned tasks for semantic search."""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from visionvault.core.models import LearnedTask
from visionvault.services.vector_store import SemanticSearch
import google.generativeai as genai

def reindex_all_tasks():
    """Re-index all learned tasks in the vector store."""
    
    # Check for API key
    gemini_api_key = os.environ.get('GEMINI_API_KEY')
    if not gemini_api_key:
        print("❌ Error: GEMINI_API_KEY is not set. Please set it to enable semantic search.")
        return
    
    try:
        # Initialize semantic search
        print("🔧 Initializing semantic search service...")
        semantic_search = SemanticSearch(api_key=gemini_api_key)
        
        # Clear existing index
        print("🗑️  Clearing existing vector index...")
        semantic_search.vector_store.clear()
        
        # Get all learned tasks
        print("📚 Loading all learned tasks from database...")
        tasks = LearnedTask.get_all()
        
        if not tasks:
            print("⚠️  No tasks found in the database.")
            return
        
        print(f"Found {len(tasks)} tasks to index")
        
        # Index each task
        indexed_count = 0
        for i, task in enumerate(tasks, 1):
            try:
                print(f"[{i}/{len(tasks)}] Indexing task: '{task.task_name}'")
                semantic_search.index_task(task)
                indexed_count += 1
            except Exception as e:
                print(f"  ❌ Failed to index task {task.task_id}: {e}")
        
        print(f"\n✅ Successfully indexed {indexed_count}/{len(tasks)} tasks!")
        print(f"📊 Vector index now contains {len(semantic_search.vector_store.metadata)} vectors")
        
    except Exception as e:
        print(f"❌ Error during re-indexing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    print("=" * 60)
    print("Re-indexing Learned Tasks for Semantic Search")
    print("=" * 60)
    reindex_all_tasks()
