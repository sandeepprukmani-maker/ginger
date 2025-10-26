import os
import json
import logging
from openai import OpenAI
from services.oauth_token_handler import get_oauth_token_with_retry

logger = logging.getLogger(__name__)

class CoverageService:
    def __init__(self):
        pass
    
    def _get_client(self):
        """Get OpenAI client with fresh OAuth token"""
        try:
            token = get_oauth_token_with_retry()
            return OpenAI(api_key=token)
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client with OAuth token: {str(e)}")
            raise Exception(f'OAuth authentication not configured. Please set OAuth environment variables (OAUTH_TOKEN_URL, OAUTH_CLIENT_ID, OAUTH_CLIENT_SECRET, OAUTH_GRANT_TYPE, OAUTH_SCOPE). Error: {str(e)}')
    
    def analyze_coverage(self, epic_data, existing_issues):
        """
        Analyze coverage of EPIC requirements against existing stories/bugs
        Returns coverage analysis with gaps and recommendations
        """
        try:
            client = self._get_client()
            prompt = self._build_coverage_analysis_prompt(epic_data, existing_issues)
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert Agile Business Analyst specialized in analyzing EPIC coverage.
                        
Your task is to:
1. Extract all functional requirements and features from the EPIC
2. Analyze existing user stories and bugs to understand what's already covered
3. Categorize coverage into: Fully Covered, Partially Covered, or Not Covered
4. For partial coverage, identify missing acceptance criteria or edge cases
5. For uncovered areas, suggest new user stories

Respond with JSON in this exact format:
{
    "epic_requirements": ["requirement 1", "requirement 2", ...],
    "coverage_analysis": {
        "fully_covered": [
            {
                "requirement": "requirement text",
                "covered_by": ["STORY-1", "STORY-2"],
                "coverage_details": "explanation of full coverage"
            }
        ],
        "partially_covered": [
            {
                "requirement": "requirement text",
                "covered_by": ["STORY-3"],
                "missing_aspects": ["missing aspect 1", "missing aspect 2"],
                "recommendation": "what needs to be added"
            }
        ],
        "not_covered": [
            {
                "requirement": "requirement text",
                "reason": "why this is not covered",
                "priority": "high|medium|low"
            }
        ]
    },
    "suggested_stories": [
        {
            "title": "story title",
            "description": "As a [role], I want [feature], so that [benefit]",
            "addresses_requirement": "which requirement this covers",
            "developer_criteria": ["criterion 1", "criterion 2"],
            "qa_criteria": ["criterion 1", "criterion 2"],
            "story_points": number,
            "priority": "high|medium|low",
            "reasoning": "why this story is needed",
            "story_type": "new_story|enhancement_to_existing"
        }
    ],
    "recommendations_for_existing": [
        {
            "story_key": "STORY-X",
            "current_issue": "what's missing or incomplete",
            "recommended_additions": ["addition 1", "addition 2"],
            "priority": "high|medium|low"
        }
    ]
}"""
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
            logger.info(f"Coverage analysis completed: {len(result.get('suggested_stories', []))} new stories suggested")
            return result
            
        except Exception as e:
            raise Exception(f"Failed to analyze coverage: {str(e)}")
    
    def _build_coverage_analysis_prompt(self, epic_data, existing_issues):
        """Build comprehensive prompt for coverage analysis"""
        prompt_parts = []
        
        prompt_parts.append("# EPIC INFORMATION\n")
        
        if epic_data.get('title'):
            prompt_parts.append(f"**EPIC Title:** {epic_data['title']}\n")
        
        if epic_data.get('description'):
            prompt_parts.append(f"**EPIC Description:**\n{epic_data['description']}\n")
        
        if epic_data.get('comments'):
            prompt_parts.append("\n**EPIC Comments:**")
            for comment in epic_data['comments']:
                prompt_parts.append(f"\n- {comment.get('author', 'Unknown')}: {comment.get('body', '')}")
        
        if epic_data.get('confluence_pages'):
            prompt_parts.append("\n\n**Confluence Documentation:**")
            for page in epic_data['confluence_pages']:
                prompt_parts.append(f"\n### {page.get('title', 'Untitled')}")
                content = page.get('content', '')
                if len(content) > 2000:
                    content = content[:2000] + "... [truncated]"
                prompt_parts.append(f"{content}")
        
        if epic_data.get('attachments'):
            prompt_parts.append("\n\n**Attached Documents:**")
            for attachment in epic_data['attachments']:
                if attachment.get('extracted_text'):
                    prompt_parts.append(f"\n### {attachment.get('filename', 'Unknown')}")
                    text = attachment['extracted_text']
                    if len(text) > 2000:
                        text = text[:2000] + "... [truncated]"
                    prompt_parts.append(f"{text}")
        
        prompt_parts.append("\n\n# EXISTING USER STORIES AND BUGS\n")
        
        if existing_issues:
            for issue in existing_issues:
                prompt_parts.append(f"\n## {issue.get('key', 'Unknown')} - {issue.get('type', 'unknown').upper()}")
                prompt_parts.append(f"**Title:** {issue.get('title', '')}")
                prompt_parts.append(f"**Status:** {issue.get('status', '')}")
                prompt_parts.append(f"**Priority:** {issue.get('priority', '')}")
                
                if issue.get('description'):
                    desc = issue['description']
                    if len(desc) > 500:
                        desc = desc[:500] + "... [truncated]"
                    prompt_parts.append(f"**Description:**\n{desc}")
                
                if issue.get('acceptance_criteria'):
                    prompt_parts.append(f"**Acceptance Criteria:**")
                    for criteria in issue['acceptance_criteria']:
                        if len(criteria) > 300:
                            criteria = criteria[:300] + "... [truncated]"
                        prompt_parts.append(f"- {criteria}")
                
                if issue.get('comments'):
                    prompt_parts.append(f"**Comments:** {len(issue['comments'])} comment(s)")
                
                prompt_parts.append("")
        else:
            prompt_parts.append("No existing user stories or bugs found linked to this EPIC.")
        
        prompt_parts.append("\n\n# TASK\n")
        prompt_parts.append("Analyze the EPIC requirements and compare them against the existing stories/bugs.")
        prompt_parts.append("Identify what's fully covered, partially covered, and not covered at all.")
        prompt_parts.append("Generate new user stories for uncovered or partially covered areas.")
        prompt_parts.append("Provide recommendations for enhancing existing stories if needed.")
        
        return '\n'.join(prompt_parts)
