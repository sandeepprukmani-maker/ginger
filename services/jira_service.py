import os
import json
import requests
from requests.auth import HTTPBasicAuth

class JiraService:
    def __init__(self):
        self.jira_url = os.environ.get('JIRA_URL')
        self.jira_email = os.environ.get('JIRA_EMAIL')
        self.jira_api_token = os.environ.get('JIRA_API_TOKEN')
    
    def _get_auth_headers(self):
        """Get authentication headers for Jira API"""
        if not self.jira_url or not self.jira_email or not self.jira_api_token:
            raise Exception('Jira credentials not configured. Please set JIRA_URL, JIRA_EMAIL, and JIRA_API_TOKEN environment variables.')
        
        return {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    
    def _get_auth(self):
        """Get basic authentication object"""
        return HTTPBasicAuth(self.jira_email, self.jira_api_token)
    
    def get_epic_details(self, epic_key):
        """Fetch EPIC details from Jira"""
        try:
            headers = self._get_auth_headers()
            auth = self._get_auth()
            
            url = f'{self.jira_url}/rest/api/3/issue/{epic_key}'
            params = {
                'expand': 'renderedFields,names,schema,transitions,operations,editmeta,changelog,versionedRepresentations',
                'fields': 'summary,description,comment,attachment,status,assignee,reporter,created,updated'
            }
            
            response = requests.get(url, headers=headers, params=params, auth=auth)
            response.raise_for_status()
            issue_data = response.json()
            
            fields = issue_data.get('fields', {})
            
            epic_info = {
                'key': epic_key,
                'title': fields.get('summary', ''),
                'description': self._extract_description(fields.get('description')),
                'comments': self._extract_comments(fields.get('comment', {})),
                'attachments': self._extract_attachments(fields.get('attachment', [])),
                'status': fields.get('status', {}).get('name', ''),
                'created': fields.get('created', ''),
                'updated': fields.get('updated', '')
            }
            
            return epic_info
            
        except Exception as e:
            raise Exception(f"Failed to fetch EPIC from Jira: {str(e)}")
    
    def _extract_description(self, description):
        """Extract text from Jira's ADF (Atlassian Document Format)"""
        if not description:
            return ''
        
        if isinstance(description, str):
            return description
        
        if isinstance(description, dict):
            return self._parse_adf_content(description)
        
        return str(description)
    
    def _parse_adf_content(self, adf):
        """Parse Atlassian Document Format to plain text"""
        if not adf or not isinstance(adf, dict):
            return ''
        
        text_parts = []
        
        def extract_text(node):
            if isinstance(node, dict):
                if node.get('type') == 'text':
                    text_parts.append(node.get('text', ''))
                
                if 'content' in node:
                    for child in node['content']:
                        extract_text(child)
            elif isinstance(node, list):
                for item in node:
                    extract_text(item)
        
        extract_text(adf)
        return ' '.join(text_parts)
    
    def _extract_comments(self, comment_data):
        """Extract comments from Jira issue"""
        comments = []
        
        if isinstance(comment_data, dict):
            comment_list = comment_data.get('comments', [])
        else:
            comment_list = comment_data if isinstance(comment_data, list) else []
        
        for comment in comment_list:
            body = comment.get('body', '')
            if isinstance(body, dict):
                body = self._parse_adf_content(body)
            
            comments.append({
                'author': comment.get('author', {}).get('displayName', 'Unknown'),
                'body': body,
                'created': comment.get('created', '')
            })
        
        return comments
    
    def _extract_attachments(self, attachments):
        """Extract attachment information"""
        attachment_list = []
        
        for attachment in attachments:
            attachment_list.append({
                'filename': attachment.get('filename', ''),
                'content_url': attachment.get('content', ''),
                'mime_type': attachment.get('mimeType', ''),
                'size': attachment.get('size', 0)
            })
        
        return attachment_list
