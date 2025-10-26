import os
import logging
from typing import List, Dict, Any
from openai import OpenAI
from services.vector_db_service import VectorDBService
from services.oauth_token_handler import get_oauth_token_with_retry
import datetime

logger = logging.getLogger(__name__)

class AMAService:
    def __init__(self, vector_db_service: VectorDBService, jira_service=None):
        self.vector_db = vector_db_service
        self.jira_service = jira_service
        self.model = "gpt-4o"
    
    def _get_client(self):
        """Get OpenAI client with fresh OAuth token"""
        try:
            token = get_oauth_token_with_retry()
            return OpenAI(api_key=token)
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client with OAuth token: {str(e)}", exc_info=True)
            return None
    
    def index_epic_data(self, epic_data: Dict[str, Any]):
        try:
            documents = []
            
            if epic_data.get('title'):
                documents.append({
                    'text': f"EPIC Title: {epic_data['title']}",
                    'source': epic_data.get('key', 'unknown'),
                    'source_type': 'jira_epic',
                    'timestamp': str(datetime.datetime.now()),
                    'title': epic_data['title'],
                    'url': epic_data.get('url', '')
                })
            
            if epic_data.get('description'):
                documents.append({
                    'text': f"EPIC Description: {epic_data['description']}",
                    'source': epic_data.get('key', 'unknown'),
                    'source_type': 'jira_epic',
                    'timestamp': str(datetime.datetime.now()),
                    'title': f"{epic_data.get('title', '')} - Description",
                    'url': epic_data.get('url', '')
                })
            
            for idx, comment in enumerate(epic_data.get('comments', [])):
                if isinstance(comment, dict):
                    comment_text = comment.get('body', str(comment))
                else:
                    comment_text = str(comment)
                
                documents.append({
                    'text': f"Comment: {comment_text}",
                    'source': f"{epic_data.get('key', 'unknown')}_comment_{idx}",
                    'source_type': 'jira_comment',
                    'timestamp': str(datetime.datetime.now()),
                    'title': f"Comment on {epic_data.get('title', 'EPIC')}",
                    'url': epic_data.get('url', '')
                })
            
            for attachment in epic_data.get('attachments', []):
                if attachment.get('extracted_text'):
                    documents.append({
                        'text': f"Attachment ({attachment.get('filename', 'unknown')}): {attachment['extracted_text']}",
                        'source': f"{epic_data.get('key', 'unknown')}_attachment",
                        'source_type': 'jira_attachment',
                        'timestamp': str(datetime.datetime.now()),
                        'title': attachment.get('filename', 'Attachment'),
                        'url': attachment.get('content_url', '')
                    })
            
            for page in epic_data.get('confluence_pages', []):
                if page.get('content'):
                    documents.append({
                        'text': f"Confluence Page ({page.get('title', 'Untitled')}): {page['content']}",
                        'source': f"confluence_{page.get('id', 'unknown')}",
                        'source_type': 'confluence',
                        'timestamp': str(datetime.datetime.now()),
                        'title': page.get('title', 'Confluence Page'),
                        'url': page.get('url', '')
                    })
            
            if self.jira_service and epic_data.get('key'):
                try:
                    logger.info(f"Fetching linked user stories and bugs for EPIC {epic_data.get('key')}")
                    linked_issues = self.jira_service.get_epic_linked_issues(epic_data.get('key'))
                    
                    for issue in linked_issues:
                        issue_type = issue.get('issue_type', 'Issue')
                        issue_key = issue.get('key', 'unknown')
                        
                        issue_summary = f"{issue_type} {issue_key}: {issue.get('summary', '')}"
                        if issue.get('description'):
                            issue_summary += f"\nDescription: {issue['description']}"
                        
                        if issue.get('acceptance_criteria'):
                            issue_summary += f"\nAcceptance Criteria: {issue['acceptance_criteria']}"
                        
                        documents.append({
                            'text': issue_summary,
                            'source': issue_key,
                            'source_type': f'jira_{issue_type.lower()}',
                            'timestamp': str(datetime.datetime.now()),
                            'title': f"{issue_type}: {issue.get('summary', '')}",
                            'url': issue.get('url', '')
                        })
                    
                    if linked_issues:
                        logger.info(f"Indexed {len(linked_issues)} linked user stories/bugs")
                except Exception as e:
                    logger.warning(f"Could not fetch linked issues: {str(e)}")
            
            if documents:
                self.vector_db.add_project_knowledge(documents)
                logger.info(f"Indexed {len(documents)} total documents from EPIC data")
                return len(documents)
            
            return 0
        except Exception as e:
            logger.error(f"Error indexing EPIC data: {str(e)}", exc_info=True)
            raise
    
    def ask_question(self, question: str, include_sources: bool = True) -> Dict[str, Any]:
        try:
            client = self._get_client()
            if not client:
                return {
                    'answer': 'OAuth authentication not configured. Please set OAuth environment variables (OAUTH_TOKEN_URL, OAUTH_CLIENT_ID, OAUTH_CLIENT_SECRET, OAUTH_GRANT_TYPE, OAUTH_SCOPE).',
                    'sources': [],
                    'confidence': 'low',
                    'error': True
                }
            
            validated_results = self.vector_db.search_validated_knowledge(question, n_results=2)
            
            if validated_results and validated_results[0].get('distance', 1) < 0.15:
                logger.info("Found validated answer with high confidence")
                answer = validated_results[0]['metadata'].get('answer', validated_results[0]['text'])
                return {
                    'answer': answer,
                    'sources': [validated_results[0]],
                    'confidence': 'high',
                    'validated': True
                }
            
            project_context = self.vector_db.search_project_knowledge(question, n_results=5)
            conversation_context = self.vector_db.search_conversation_memory(question, n_results=3)
            
            context_parts = []
            sources = []
            
            if validated_results:
                context_parts.append("=== Previously Validated Knowledge ===")
                for result in validated_results:
                    context_parts.append(result['text'])
                    sources.append({
                        'type': 'validated',
                        'content': result['text'],
                        'metadata': result.get('metadata', {})
                    })
            
            if project_context:
                context_parts.append("\n=== Project Knowledge ===")
                for result in project_context:
                    context_parts.append(result['text'])
                    sources.append({
                        'type': 'project',
                        'content': result['text'],
                        'metadata': result.get('metadata', {})
                    })
            
            if conversation_context:
                context_parts.append("\n=== Previous Conversations ===")
                for result in conversation_context:
                    context_parts.append(result['text'])
                    sources.append({
                        'type': 'conversation',
                        'content': result['text'],
                        'metadata': result.get('metadata', {})
                    })
            
            context = "\n".join(context_parts)
            
            system_prompt = """You are an AI assistant with deep knowledge about the project, EPICs, user stories, and all related documentation.

Your role is to:
1. Answer questions accurately based on the provided context
2. Maintain consistency with previous answers
3. Reference specific sources when possible
4. Admit uncertainty if the context doesn't contain the answer
5. Provide clear, concise, and helpful responses

If the context doesn't contain enough information to answer the question, say so clearly and suggest what additional information might be needed."""

            user_prompt = f"""Context from project knowledge and previous conversations:

{context}

Question: {question}

Please provide a clear, accurate answer based on the context above. If you reference specific information, mention the source (EPIC, Confluence page, comment, etc.)."""

            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            answer = response.choices[0].message.content
            
            self.vector_db.add_conversation(question, answer, context[:500])
            
            confidence = 'high' if project_context or validated_results else 'medium'
            if not project_context and not validated_results and not conversation_context:
                confidence = 'low'
            
            result = {
                'answer': answer,
                'confidence': confidence,
                'validated': False
            }
            
            if include_sources:
                result['sources'] = sources[:5]
            
            return result
            
        except Exception as e:
            logger.error(f"Error in ask_question: {str(e)}", exc_info=True)
            return {
                'answer': f'Error processing question: {str(e)}',
                'sources': [],
                'confidence': 'low',
                'error': True
            }
    
    def submit_feedback(self, question: str, answer: str, feedback_type: str, corrected_answer: str = None):
        try:
            if feedback_type == 'accept':
                self.vector_db.add_validated_knowledge(question, answer, {
                    'feedback_type': 'accepted',
                    'original_answer': answer
                })
                logger.info(f"User accepted answer for: {question[:50]}...")
                
            elif feedback_type == 'correct' and corrected_answer:
                self.vector_db.add_validated_knowledge(question, corrected_answer, {
                    'feedback_type': 'corrected',
                    'original_answer': answer,
                    'corrected_answer': corrected_answer
                })
                logger.info(f"User corrected answer for: {question[:50]}...")
                
            elif feedback_type == 'reject':
                logger.info(f"User rejected answer for: {question[:50]}...")
            
            return {'success': True, 'message': 'Feedback recorded successfully'}
            
        except Exception as e:
            logger.error(f"Error submitting feedback: {str(e)}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def get_stats(self) -> Dict[str, Any]:
        try:
            stats = self.vector_db.get_collection_stats()
            client = self._get_client()
            return {
                'knowledge_base_size': stats.get('project_knowledge_count', 0),
                'conversations_stored': stats.get('conversation_count', 0),
                'validated_answers': stats.get('validated_knowledge_count', 0),
                'status': 'active' if client else 'oauth_not_configured'
            }
        except Exception as e:
            logger.error(f"Error getting stats: {str(e)}", exc_info=True)
            return {}
