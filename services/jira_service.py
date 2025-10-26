import os
import json
import requests

class JiraService:
    def __init__(self):
        self.connection_settings = None
    
    def _get_access_token(self):
        """Get access token from Replit's connector API"""
        if self.connection_settings and self.connection_settings.get('settings', {}).get('expires_at'):
            from datetime import datetime
            expires_at = self.connection_settings['settings']['expires_at']
            if datetime.fromisoformat(expires_at.replace('Z', '+00:00')).timestamp() * 1000 > datetime.now().timestamp() * 1000:
                return self.connection_settings['settings'].get('access_token')
        
        hostname = os.environ.get('REPLIT_CONNECTORS_HOSTNAME')
        x_replit_token = None
        
        if os.environ.get('REPL_IDENTITY'):
            x_replit_token = 'repl ' + os.environ.get('REPL_IDENTITY')
        elif os.environ.get('WEB_REPL_RENEWAL'):
            x_replit_token = 'depl ' + os.environ.get('WEB_REPL_RENEWAL')
        
        if not x_replit_token:
            raise Exception('X_REPLIT_TOKEN not found for repl/depl')
        
        url = f'https://{hostname}/api/v2/connection?include_secrets=true&connector_names=jira'
        headers = {
            'Accept': 'application/json',
            'X_REPLIT_TOKEN': x_replit_token
        }
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        self.connection_settings = data.get('items', [{}])[0]
        
        access_token = self.connection_settings.get('settings', {}).get('access_token') or \
                      self.connection_settings.get('settings', {}).get('oauth', {}).get('credentials', {}).get('access_token')
        site_url = self.connection_settings.get('settings', {}).get('site_url')
        
        if not access_token or not site_url:
            raise Exception('Jira not connected')
        
        return {'access_token': access_token, 'site_url': site_url}
    
    def get_epic_details(self, epic_key):
        """Fetch EPIC details from Jira"""
        try:
            auth_data = self._get_access_token()
            access_token = auth_data['access_token']
            site_url = auth_data['site_url']
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
            
            url = f'{site_url}/rest/api/3/issue/{epic_key}'
            params = {
                'expand': 'renderedFields,names,schema,transitions,operations,editmeta,changelog,versionedRepresentations',
                'fields': 'summary,description,comment,attachment,status,assignee,reporter,created,updated'
            }
            
            response = requests.get(url, headers=headers, params=params)
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
