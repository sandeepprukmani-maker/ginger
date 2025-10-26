import os
import json
from openai import OpenAI

class AIService:
    def __init__(self):
        self.api_key = os.environ.get('OPENAI_API_KEY')
        if not self.api_key:
            raise Exception('OPENAI_API_KEY not found in environment variables')
        
        self.client = OpenAI(api_key=self.api_key)
    
    def generate_user_stories(self, epic_data, additional_context=''):
        """Generate user stories from EPIC data using AI"""
        try:
            prompt = self._build_story_generation_prompt(epic_data, additional_context)
            
            # the newest OpenAI model is "gpt-5" which was released August 7, 2025.
            # do not change this unless explicitly requested by the user
            response = self.client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert Agile Business Analyst specialized in writing clear, actionable user stories. "
                                 "Generate well-structured user stories with separate developer and QA acceptance criteria. "
                                 "Respond with JSON in this format: "
                                 "{'stories': [{'title': 'story title', 'description': 'As a [role], I want [feature], so that [benefit]', "
                                 "'developer_criteria': ['criterion 1', 'criterion 2'], 'qa_criteria': ['criterion 1', 'criterion 2'], "
                                 "'story_points': number, 'priority': 'high|medium|low', 'reasoning': 'why this story is needed'}]}"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"},
                max_completion_tokens=8192
            )
            
            result = json.loads(response.choices[0].message.content)
            return result.get('stories', [])
            
        except Exception as e:
            raise Exception(f"Failed to generate user stories: {str(e)}")
    
    def _build_story_generation_prompt(self, epic_data, additional_context):
        """Build comprehensive prompt for story generation"""
        prompt_parts = []
        
        prompt_parts.append("Please analyze the following EPIC and generate comprehensive user stories:\n")
        
        if epic_data.get('title'):
            prompt_parts.append(f"\n**EPIC Title:** {epic_data['title']}\n")
        
        if epic_data.get('description'):
            prompt_parts.append(f"\n**EPIC Description:**\n{epic_data['description']}\n")
        
        if epic_data.get('comments'):
            prompt_parts.append("\n**Comments:**")
            for comment in epic_data['comments']:
                prompt_parts.append(f"\n- {comment.get('author', 'Unknown')}: {comment.get('body', '')}")
        
        if epic_data.get('confluence_pages'):
            prompt_parts.append("\n**Confluence Documentation:**")
            for page in epic_data['confluence_pages']:
                prompt_parts.append(f"\n### {page.get('title', 'Untitled')}")
                prompt_parts.append(f"{page.get('content', '')}")
        
        if epic_data.get('attachments'):
            prompt_parts.append("\n**Attached Documents:**")
            for attachment in epic_data['attachments']:
                if attachment.get('extracted_text'):
                    prompt_parts.append(f"\n### {attachment.get('filename', 'Unknown')}")
                    prompt_parts.append(f"{attachment['extracted_text']}")
        
        if additional_context:
            prompt_parts.append(f"\n**Additional Context:**\n{additional_context}\n")
        
        prompt_parts.append("\n\nGenerate user stories that:")
        prompt_parts.append("1. Follow the format: 'As a [role], I want [feature], so that [benefit]'")
        prompt_parts.append("2. Include separate developer acceptance criteria (technical validations, data handling, edge cases)")
        prompt_parts.append("3. Include separate QA acceptance criteria (functional checks, UI validations, boundary tests)")
        prompt_parts.append("4. Are non-overlapping and cover all functionalities")
        prompt_parts.append("5. Include estimated story points and priority")
        prompt_parts.append("6. Provide reasoning for why each story is needed")
        
        return '\n'.join(prompt_parts)
    
    def answer_question(self, epic_data, question):
        """Answer clarifying questions about the EPIC"""
        try:
            context = self._build_epic_context(epic_data)
            
            # the newest OpenAI model is "gpt-5" which was released August 7, 2025.
            # do not change this unless explicitly requested by the user
            response = self.client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful AI assistant analyzing an Agile EPIC. "
                                 "Answer questions clearly and concisely based on the EPIC information provided."
                    },
                    {
                        "role": "user",
                        "content": f"EPIC Context:\n{context}\n\nQuestion: {question}"
                    }
                ],
                max_completion_tokens=2048
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            raise Exception(f"Failed to answer question: {str(e)}")
    
    def _build_epic_context(self, epic_data):
        """Build context string from EPIC data"""
        context_parts = []
        
        if epic_data.get('title'):
            context_parts.append(f"Title: {epic_data['title']}")
        
        if epic_data.get('description'):
            context_parts.append(f"\nDescription:\n{epic_data['description']}")
        
        if epic_data.get('comments'):
            context_parts.append("\nComments:")
            for comment in epic_data['comments'][:5]:
                context_parts.append(f"- {comment.get('body', '')}")
        
        return '\n'.join(context_parts)
    
    def format_stories_as_text(self, stories):
        """Format stories as readable text"""
        formatted_parts = []
        
        for i, story in enumerate(stories, 1):
            formatted_parts.append(f"\n{'='*80}")
            formatted_parts.append(f"USER STORY #{i}: {story.get('title', 'Untitled')}")
            formatted_parts.append(f"{'='*80}\n")
            
            formatted_parts.append(f"Description:\n{story.get('description', '')}\n")
            
            formatted_parts.append(f"Priority: {story.get('priority', 'medium').upper()}")
            formatted_parts.append(f"Story Points: {story.get('story_points', 'TBD')}\n")
            
            if story.get('reasoning'):
                formatted_parts.append(f"Reasoning:\n{story['reasoning']}\n")
            
            formatted_parts.append("Developer Acceptance Criteria:")
            for criterion in story.get('developer_criteria', []):
                formatted_parts.append(f"  - {criterion}")
            
            formatted_parts.append("\nQA Acceptance Criteria:")
            for criterion in story.get('qa_criteria', []):
                formatted_parts.append(f"  - {criterion}")
            
            formatted_parts.append("")
        
        return '\n'.join(formatted_parts)
