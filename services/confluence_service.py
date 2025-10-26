import os
import json
import requests
import logging
from bs4 import BeautifulSoup
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class ConfluenceService:
    def __init__(self):
        self.confluence_url = os.environ.get('CONFLUENCE_URL')
        self.confluence_email = os.environ.get('CONFLUENCE_EMAIL')
        self.confluence_api_token = os.environ.get('CONFLUENCE_API_TOKEN')
    
    def _check_configured(self):
        """Check if Confluence credentials are configured"""
        if not self.confluence_url or not self.confluence_email or not self.confluence_api_token:
            raise Exception('Confluence credentials not configured. Please set CONFLUENCE_URL, CONFLUENCE_EMAIL, and CONFLUENCE_API_TOKEN environment variables.')
    
    def _get_auth_headers(self):
        """Get authentication headers for Confluence API"""
        self._check_configured()
        return {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    
    def _get_auth(self):
        """Get basic authentication object"""
        self._check_configured()
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
    
    def get_child_pages(self, page_id):
        """Get child pages of a Confluence page with pagination support"""
        try:
            headers = self._get_auth_headers()
            auth = self._get_auth()
            
            child_page_ids = []
            start = 0
            limit = 100
            
            while True:
                url = f'{self.confluence_url}/wiki/rest/api/content/{page_id}/child/page'
                params = {
                    'limit': limit,
                    'start': start
                }
                
                response = requests.get(url, headers=headers, params=params, auth=auth)
                response.raise_for_status()
                data = response.json()
                
                results = data.get('results', [])
                for result in results:
                    child_page_ids.append(result.get('id'))
                
                if len(results) < limit or data.get('size', 0) < limit:
                    break
                
                start += limit
            
            return child_page_ids
            
        except Exception as e:
            logger.error(f"Failed to fetch child pages for {page_id}: {str(e)}", exc_info=True)
            return []
    
    def resolve_display_url_to_page_id(self, space_key, page_title):
        """Resolve a Confluence /display/ URL to a page ID"""
        try:
            headers = self._get_auth_headers()
            auth = self._get_auth()
            
            url = f'{self.confluence_url}/wiki/rest/api/content'
            params = {
                'type': 'page',
                'spaceKey': space_key,
                'title': page_title.replace('+', ' '),
                'limit': 1
            }
            
            response = requests.get(url, headers=headers, params=params, auth=auth)
            response.raise_for_status()
            data = response.json()
            
            results = data.get('results', [])
            if results:
                page_id = results[0].get('id')
                logger.info(f"Resolved /display/ URL to page ID: {page_id}")
                return page_id
            else:
                logger.warning(f"Could not resolve page in space {space_key} with title {page_title}")
                return None
                
        except Exception as e:
            logger.error(f"Error resolving display URL: {str(e)}", exc_info=True)
            return None
    
    def get_page_with_children(self, page_id, max_depth=3, current_depth=0, visited=None):
        """Recursively fetch a Confluence page and its children"""
        if visited is None:
            visited = set()
        
        if page_id in visited or current_depth > max_depth:
            return []
        
        visited.add(page_id)
        pages = []
        
        try:
            page_info = self.get_page_content(page_id)
            pages.append(page_info)
            logger.info(f"Fetched Confluence page: {page_info.get('title', 'Unknown')} (ID: {page_id})")
            
            if current_depth < max_depth:
                child_page_ids = self.get_child_pages(page_id)
                logger.info(f"Found {len(child_page_ids)} child pages for page {page_id}")
                
                for child_id in child_page_ids:
                    child_pages = self.get_page_with_children(
                        child_id, 
                        max_depth, 
                        current_depth + 1, 
                        visited
                    )
                    pages.extend(child_pages)
            
            return pages
            
        except Exception as e:
            logger.error(f"Error fetching page {page_id} with children: {str(e)}", exc_info=True)
            return pages
