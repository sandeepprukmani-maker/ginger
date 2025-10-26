import os
import logging
from flask import Flask, render_template, request, jsonify, session
from dotenv import load_dotenv
from services.jira_service import JiraService
from services.confluence_service import ConfluenceService
from services.document_processor import DocumentProcessor
from services.ai_service import AIService
from services.coverage_service import CoverageService
from services.vector_db_service import VectorDBService
from services.ama_service import AMAService
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
coverage_service = CoverageService()
vector_db_service = VectorDBService()
ama_service = AMAService(vector_db_service, jira_service)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/analyze-epic', methods=['POST'])
def analyze_epic():
    try:
        data = request.json
        epic_key = data.get('epic_key', '').strip()
        confluence_page_ids = data.get('confluence_page_ids', [])
        
        logger.info(f"Analyzing EPIC - Key: {epic_key}, Confluence IDs: {confluence_page_ids}")
        
        if not epic_key:
            return jsonify({'error': 'Please provide a Jira EPIC key'}), 400
        
        epic_data = {
            'title': '',
            'description': '',
            'comments': [],
            'attachments': [],
            'confluence_pages': [],
            'source': 'jira'
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

@app.route('/api/analyze-coverage', methods=['POST'])
def analyze_coverage():
    try:
        data = request.json
        epic_key = data.get('epic_key', '').strip()
        
        if not epic_key:
            return jsonify({'error': 'Please provide a Jira EPIC key'}), 400
        
        epic_data = session.get('epic_data')
        if not epic_data or epic_data.get('key') != epic_key:
            return jsonify({'error': 'EPIC not analyzed yet. Please analyze the EPIC first.'}), 400
        
        logger.info(f"Analyzing coverage for EPIC {epic_key}")
        
        existing_issues = jira_service.get_epic_linked_issues(epic_key)
        
        coverage_analysis = coverage_service.analyze_coverage(epic_data, existing_issues)
        
        session['coverage_analysis'] = coverage_analysis
        session['existing_issues'] = existing_issues
        
        return jsonify({
            'success': True,
            'coverage_analysis': coverage_analysis,
            'existing_issues_count': len(existing_issues)
        })
        
    except Exception as e:
        logger.error(f"Error in analyze_coverage: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/approve-coverage-stories', methods=['POST'])
def approve_coverage_stories():
    try:
        data = request.json
        approved_story_indices = data.get('approved_indices', [])
        
        coverage_analysis = session.get('coverage_analysis')
        if not coverage_analysis:
            return jsonify({'error': 'No coverage analysis found'}), 400
        
        suggested_stories = coverage_analysis.get('suggested_stories', [])
        approved_stories = [suggested_stories[i] for i in approved_story_indices if i < len(suggested_stories)]
        
        session['generated_stories'] = approved_stories
        
        return jsonify({
            'success': True,
            'approved_count': len(approved_stories),
            'stories': approved_stories
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/ama')
def ama():
    return render_template('ama.html')

@app.route('/api/ama/stats', methods=['GET'])
def ama_stats():
    try:
        stats = ama_service.get_stats()
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        logger.error(f"Error getting AMA stats: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ama/ask', methods=['POST'])
def ama_ask():
    try:
        data = request.json
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({'success': False, 'error': 'Question is required'}), 400
        
        result = ama_service.ask_question(question)
        
        return jsonify({
            'success': not result.get('error', False),
            'answer': result.get('answer', ''),
            'confidence': result.get('confidence', 'low'),
            'validated': result.get('validated', False),
            'sources': result.get('sources', [])
        })
    except Exception as e:
        logger.error(f"Error in AMA ask: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ama/feedback', methods=['POST'])
def ama_feedback():
    try:
        data = request.json
        question = data.get('question', '').strip()
        answer = data.get('answer', '').strip()
        feedback_type = data.get('feedback_type', 'accept')
        corrected_answer = data.get('corrected_answer', '').strip()
        
        if not question or not answer:
            return jsonify({'success': False, 'error': 'Question and answer are required'}), 400
        
        result = ama_service.submit_feedback(question, answer, feedback_type, corrected_answer)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error submitting AMA feedback: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ama/index-epic', methods=['POST'])
def ama_index_epic():
    try:
        epic_data = session.get('epic_data')
        
        if not epic_data:
            return jsonify({
                'success': False,
                'error': 'No EPIC data found. Please analyze an EPIC first from the Dashboard.'
            }), 400
        
        documents_added = ama_service.index_epic_data(epic_data)
        
        return jsonify({
            'success': True,
            'documents_added': documents_added,
            'message': f'Successfully indexed {documents_added} documents'
        })
    except Exception as e:
        logger.error(f"Error indexing EPIC for AMA: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
