import os
import json
import requests
from bs4 import BeautifulSoup
from requests.auth import HTTPBasicAuth

class ConfluenceService:
    def __init__(self):
        self.confluence_url = os.environ.get('CONFLUENCE_URL')
        self.confluence_email = os.environ.get('CONFLUENCE_EMAIL')
        self.confluence_api_token = os.environ.get('CONFLUENCE_API_TOKEN')
    
    def _get_auth_headers(self):
        """Get authentication headers for Confluence API"""
        if not self.confluence_url or not self.confluence_email or not self.confluence_api_token:
            raise Exception('Confluence credentials not configured. Please set CONFLUENCE_URL, CONFLUENCE_EMAIL, and CONFLUENCE_API_TOKEN environment variables.')
        
        return {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    
    def _get_auth(self):
        """Get basic authentication object"""
        return HTTPBasicAuth(self.confluence_email, self.confluence_api_token)
    
    def get_page_content(self, page_id):
        """Fetch Confluence page content"""
        try:
            headers = self._get_auth_headers()
            auth = self._get_auth()
            
            url = f'{self.confluence_url}/wiki/rest/api/content/{page_id}'
            params = {
                'expand': 'body.storage,version,space'
            }
            
            response = requests.get(url, headers=headers, params=params, auth=auth)
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
