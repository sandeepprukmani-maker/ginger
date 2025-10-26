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
- `REPLIT_CONNECTORS_HOSTNAME` - Replit connector hostname (auto-provided)
- `REPL_IDENTITY` or `WEB_REPL_RENEWAL` - Replit authentication tokens (auto-provided)

## Integrations Configured
1. **Jira** (connection:conn_jira_01K8GZ8J55J7P7BJW98C8HA6F5)
   - Permissions: manage projects, read/write work items
   - Used for fetching EPIC details, comments, and attachments

2. **Confluence** (connection:conn_confluence_01K8GZGVDEQVV2VE6NN1AXJCRX)
   - Permissions: read/write content, search
   - Used for fetching linked documentation pages

3. **OpenAI** (blueprint:python_openai)
   - Model: GPT-5 (latest as of August 2025)
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
- All AI calls use GPT-5 (not GPT-4 or GPT-4o)
- Jira and Confluence use OAuth2 via Replit connectors
- Access tokens are refreshed automatically when expired
- Sessions store EPIC data and generated stories in-memory
- Document processing uses temporary files for security
- Frontend uses Bootstrap 5 for responsive design
