import os
import json
import requests
from bs4 import BeautifulSoup

class ConfluenceService:
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
        
        url = f'https://{hostname}/api/v2/connection?include_secrets=true&connector_names=confluence'
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
            raise Exception('Confluence not connected')
        
        return {'access_token': access_token, 'site_url': site_url}
    
    def get_page_content(self, page_id):
        """Fetch Confluence page content"""
        try:
            auth_data = self._get_access_token()
            access_token = auth_data['access_token']
            site_url = auth_data['site_url']
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Accept': 'application/json'
            }
            
            url = f'{site_url}/wiki/rest/api/content/{page_id}'
            params = {
                'expand': 'body.storage,version,space'
            }
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            page_data = response.json()
            
            page_info = {
                'id': page_id,
                'title': page_data.get('title', ''),
                'content': self._extract_html_content(page_data.get('body', {}).get('storage', {}).get('value', '')),
                'space': page_data.get('space', {}).get('name', ''),
                'version': page_data.get('version', {}).get('number', 1)
            }
            
            return page_info
            
        except Exception as e:
            raise Exception(f"Failed to fetch Confluence page: {str(e)}")
    
    def _extract_html_content(self, html_content):
        """Extract plain text from HTML content"""
        if not html_content:
            return ''
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        for script in soup(["script", "style"]):
            script.decompose()
        
        text = soup.get_text(separator='\n')
        
        lines = [line.strip() for line in text.splitlines()]
        text = '\n'.join(line for line in lines if line)
        
        return text
