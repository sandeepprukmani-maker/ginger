import os
import logging
from flask import Flask, render_template, request, jsonify, session
from dotenv import load_dotenv
from services.jira_service import JiraService
from services.confluence_service import ConfluenceService
from services.document_processor import DocumentProcessor
from services.ai_service import AIService
import secrets

load_dotenv()

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get('SESSION_SECRET', secrets.token_hex(32))

jira_service = JiraService()
confluence_service = ConfluenceService()
document_processor = DocumentProcessor()
ai_service = AIService()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/analyze-epic', methods=['POST'])
def analyze_epic():
    try:
        data = request.json
        epic_key = data.get('epic_key', '').strip()
        manual_text = data.get('manual_text', '').strip()
        confluence_page_ids = data.get('confluence_page_ids', [])
        
        logger.info(f"Analyzing EPIC - Key: {epic_key}, Manual: {bool(manual_text)}, Confluence IDs: {confluence_page_ids}")
        
        if not epic_key and not manual_text:
            return jsonify({'error': 'Please provide either a Jira EPIC key or manual text'}), 400
        
        epic_data = {
            'title': '',
            'description': '',
            'comments': [],
            'attachments': [],
            'confluence_pages': [],
            'source': 'manual' if manual_text else 'jira'
        }
        
        if epic_key:
            epic_info = jira_service.get_epic_details(epic_key)
            logger.debug(f"Received EPIC info from Jira: {epic_info}")
            epic_data.update(epic_info)
            
            discovered_links = epic_info.get('confluence_page_ids', {})
            if isinstance(discovered_links, dict):
                discovered_page_ids = discovered_links.get('page_ids', [])
                display_urls = discovered_links.get('display_urls', [])
                
                if discovered_page_ids:
                    logger.info(f"Discovered {len(discovered_page_ids)} Confluence page IDs in EPIC")
                    confluence_page_ids.extend(discovered_page_ids)
                
                if display_urls:
                    logger.info(f"Discovered {len(display_urls)} Confluence /display/ URLs in EPIC")
                    for space_key, page_title in display_urls:
                        page_id = confluence_service.resolve_display_url_to_page_id(space_key, page_title)
                        if page_id:
                            confluence_page_ids.append(page_id)
            elif isinstance(discovered_links, list):
                confluence_page_ids.extend(discovered_links)
            
            if epic_data.get('attachments'):
                auth = jira_service._get_auth()
                for attachment in epic_data['attachments']:
                    if attachment.get('content_url'):
                        extracted_text = document_processor.process_attachment(
                            attachment['content_url'],
                            attachment['filename'],
                            auth
                        )
                        attachment['extracted_text'] = extracted_text
        else:
            epic_data['description'] = manual_text
            epic_data['title'] = 'Manual EPIC Entry'
        
        confluence_page_ids = list(set(confluence_page_ids))
        
        if confluence_page_ids:
            logger.info(f"Fetching {len(confluence_page_ids)} Confluence pages with recursive crawling")
            for page_id in confluence_page_ids:
                try:
                    pages = confluence_service.get_page_with_children(page_id, max_depth=2)
                    epic_data['confluence_pages'].extend(pages)
                    logger.info(f"Fetched {len(pages)} pages (including children) for page ID {page_id}")
                except Exception as e:
                    logger.error(f"Error fetching Confluence page {page_id}: {str(e)}")
                    epic_data['confluence_pages'].append({
                        'id': page_id,
                        'title': 'Error',
                        'content': f'Failed to fetch: {str(e)}',
                        'error': True
                    })
        
        session['epic_data'] = epic_data
        
        return jsonify({
            'success': True,
            'epic_data': epic_data,
            'message': 'EPIC data retrieved successfully'
        })
        
    except Exception as e:
        logger.error(f"Error in analyze_epic: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-stories', methods=['POST'])
def generate_stories():
    try:
        epic_data = session.get('epic_data')
        if not epic_data:
            return jsonify({'error': 'No EPIC data found. Please analyze an EPIC first.'}), 400
        
        data = request.json
        additional_context = data.get('additional_context', '')
        
        stories = ai_service.generate_user_stories(epic_data, additional_context)
        
        session['generated_stories'] = stories
        
        return jsonify({
            'success': True,
            'stories': stories
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ask-clarification', methods=['POST'])
def ask_clarification():
    try:
        data = request.json
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({'error': 'Question is required'}), 400
        
        epic_data = session.get('epic_data')
        if not epic_data:
            return jsonify({'error': 'No EPIC data found'}), 400
        
        answer = ai_service.answer_question(epic_data, question)
        
        return jsonify({
            'success': True,
            'answer': answer
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/export-stories', methods=['POST'])
def export_stories():
    try:
        stories = session.get('generated_stories', [])
        if not stories:
            return jsonify({'error': 'No stories to export'}), 400
        
        data = request.json
        export_format = data.get('format', 'json')
        
        if export_format == 'json':
            return jsonify({
                'success': True,
                'data': stories
            })
        elif export_format == 'text':
            formatted_text = ai_service.format_stories_as_text(stories)
            return jsonify({
                'success': True,
                'data': formatted_text
            })
        else:
            return jsonify({'error': 'Invalid export format'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/update-story', methods=['POST'])
def update_story():
    try:
        data = request.json
        story_index = data.get('index')
        updated_story = data.get('story')
        
        stories = session.get('generated_stories', [])
        if story_index is None or story_index >= len(stories):
            return jsonify({'error': 'Invalid story index'}), 400
        
        stories[story_index] = updated_story
        session['generated_stories'] = stories
        
        return jsonify({
            'success': True,
            'message': 'Story updated successfully'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
