# iDraft - AI-Powered Story Generator

## Overview
iDraft is an advanced AI-powered Agile assistant built using Python and Flask. It intelligently reads, understands, and processes EPICs, Confluence pages, documents, and attachments to automatically generate clear, complete user stories with detailed acceptance criteria for both developers and QA teams.

## Project Purpose
Transform the manual, time-consuming process of writing user stories from EPICs into an automated, AI-driven workflow that:
- Reads EPICs from Jira with all metadata, comments, and attachments
- Fetches linked Confluence documentation
- Processes PDF, DOCX, and TXT attachments
- Generates well-structured user stories with separate developer and QA acceptance criteria
- Provides an interactive interface for clarifying questions
- Offers a staging area to review and approve stories before export

## Current State
**Status**: MVP Implementation Complete

The application includes:
- Flask backend with RESTful API endpoints
- Jira integration for EPIC ingestion
- Confluence integration for documentation fetching
- Document processing for PDF, DOCX, and TXT files
- OpenAI GPT-5 integration for AI-powered story generation
- Responsive web interface with Bootstrap 5
- Story review dashboard with staging area
- Export functionality (JSON and formatted text)
- Conversational AI interface for Q&A

## Recent Changes
- **2025-10-26**: Migration and integration setup completed
  - **Migrated**: Successfully migrated to Replit environment
  - **Configured**: All integrations (Jira, Confluence, OpenAI) are active
  - **Cleaned**: Removed unused navigation items from sidebar
  - **Verified**: Application running successfully on port 5000

- **2025-10-26**: Complete redesign with dark theme UI
  - **Redesigned**: Complete UI overhaul with dark theme and sidebar navigation
  - **Rebranded**: Changed from EpicMind to iDraft
  - **Enhanced**: Modern dark theme with purple accents
  - **Improved**: Clean sidebar navigation with sections
  - **Added**: Professional dashboard layout matching industry standards
  
- **2025-10-26**: Initial project setup and MVP completion
  - Created Flask application structure with modular services
  - Implemented Jira and Confluence integration services using Replit connectors
  - Built AI service using OpenAI GPT-5 for story generation
  - Created document processor for PDF/DOCX/TXT files
  - Added conversational AI interface for clarifying questions
  - Implemented story staging and export features
  - Integrated attachment processing in analyze-epic endpoint
  - Added Confluence page fetching and content extraction
  - Frontend supports optional Confluence page IDs input
  - All MVP features working and architect-reviewed

## Project Architecture

### Backend Structure
```
app.py                      # Main Flask application with routes
services/
  ├── __init__.py          # Services module
  ├── jira_service.py      # Jira API integration
  ├── confluence_service.py # Confluence API integration
  ├── document_processor.py # Document text extraction
  └── ai_service.py        # OpenAI integration for story generation
```

### Frontend Structure
```
templates/
  ├── base.html            # Base template with Bootstrap
  └── index.html           # Main application interface
static/
  ├── css/
  │   └── style.css        # Custom styles
  └── js/
      └── main.js          # Frontend JavaScript logic
```

### Key Technologies
- **Backend**: Python 3.11, Flask 3.1.2
- **Integrations**: Jira API, Confluence API (via Replit connectors)
- **AI**: OpenAI GPT-5 (latest model as of August 2025)
- **Document Processing**: PyPDF2, python-docx
- **Frontend**: Bootstrap 5, Vanilla JavaScript
- **Session Management**: Flask sessions (server-side)

### API Endpoints
- `GET /` - Main application interface
- `POST /api/analyze-epic` - Analyze EPIC from Jira or manual text
- `POST /api/generate-stories` - Generate user stories using AI
- `POST /api/ask-clarification` - Ask questions about the EPIC
- `POST /api/export-stories` - Export stories in JSON or text format
- `POST /api/update-story` - Update individual stories

## Environment Variables
- `OPENAI_API_KEY` - OpenAI API key for GPT-5 access
- `SESSION_SECRET` - Flask session secret key
- `JIRA_URL` - Jira instance URL (e.g., https://your-domain.atlassian.net)
- `JIRA_EMAIL` - Jira account email for authentication
- `JIRA_API_TOKEN` - Jira API token for authentication
- `CONFLUENCE_URL` - Confluence instance URL (e.g., https://your-domain.atlassian.net)
- `CONFLUENCE_EMAIL` - Confluence account email for authentication
- `CONFLUENCE_API_TOKEN` - Confluence API token for authentication

## Integrations Configured
1. **Jira** - Basic Authentication ⚠️ Needs Setup
   - Using email + API token authentication
   - Used for fetching EPIC details, comments, and attachments
   - Note: User chose not to use Replit connector integration

2. **Confluence** - Basic Authentication ⚠️ Needs Setup
   - Using email + API token authentication
   - Used for fetching linked documentation pages
   - Note: User chose not to use Replit connector integration

3. **OpenAI** (blueprint:python_openai) ✅ Active
   - Model: GPT-4o-mini (cost-effective model)
   - API Key configured
   - Used for story generation and conversational AI

## User Workflow
1. User provides EPIC information (Jira key or manual text)
2. System analyzes EPIC and displays summary
3. User can ask clarifying questions via AI chat
4. User triggers story generation with optional context
5. AI generates user stories with dev/QA criteria
6. User reviews stories in staging dashboard
7. User exports stories as JSON or formatted text

## Next Phase Features
- Direct Jira integration to create/update stories
- Advanced document processing (OCR, Excel, recursive Confluence)
- Intelligent refinement for existing EPICs
- Learning system for team writing style
- Validation engine with duplicate detection
- Slack/Teams integration

## Development Notes
- All AI calls use GPT-4o-mini for cost-effective story generation
- Jira and Confluence use basic authentication (email + API token)
- Access tokens are refreshed automatically when expired
- Sessions store EPIC data and generated stories in-memory
- Document processing uses temporary files for security
- Frontend uses Bootstrap 5 for responsive design
