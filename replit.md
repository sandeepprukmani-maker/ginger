# iDraft - AI-Powered Story Generator

## Overview
iDraft is an advanced AI-powered Agile assistant designed to automate the creation of user stories and acceptance criteria from various project artifacts. It reads and processes EPICs, Confluence pages, documents (PDF, DOCX, TXT, XLSX, images), and attachments to generate clear, complete user stories tailored for both developers and QA teams. The project aims to transform manual story writing into an efficient, AI-driven workflow, providing an interactive interface for clarification, a staging area for review, and export functionality. iDraft also includes an "Ask Me Anything" (AMA) feature for conversational AI and a coverage analysis tool to identify gaps in existing stories.

## User Preferences
I prefer simple language and clear explanations. I want iterative development with frequent feedback loops. Please ask before making major architectural changes or introducing new significant dependencies. I prefer to review and approve AI-generated content in a staging area before it's finalized or exported. I value a clean, professional UI with a dark theme. I do not want the AI to directly create or update stories in Jira without my explicit approval.

## Environment Configuration

### .env File Setup
The project uses environment variables stored in a `.env` file for configuration. All service modules load environment variables from this file at startup using `python-dotenv`.

**Loading Order**:
1. `app.py` loads `.env` **before** importing any service modules
2. Each service module (`jira_service.py`, `confluence_service.py`, etc.) also calls `load_dotenv()` for standalone usage
3. `oauth_token_handler.py` uses `load_dotenv(override=True)` to ensure fresh token configuration

**Required Environment Variables**:
- `JIRA_URL`: Your Atlassian Jira instance URL (e.g., https://yourcompany.atlassian.net)
- `JIRA_EMAIL`: Email address for Jira authentication
- `JIRA_API_TOKEN`: Jira API token for authentication
- `CONFLUENCE_URL`: Your Atlassian Confluence instance URL
- `CONFLUENCE_EMAIL`: Email address for Confluence authentication
- `CONFLUENCE_API_TOKEN`: Confluence API token for authentication
- `SESSION_SECRET`: Flask session secret key for secure sessions
- `OAUTH_TOKEN_URL`: OAuth provider token endpoint URL
- `OAUTH_CLIENT_ID`: OAuth client ID for OpenAI authentication
- `OAUTH_CLIENT_SECRET`: OAuth client secret
- `OAUTH_GRANT_TYPE`: OAuth grant type (typically `client_credentials`)
- `OAUTH_SCOPE`: Required OAuth scopes
- `GW_BASE_URL`: Gateway base URL for API requests (optional)
- `DATABASE_URL`: PostgreSQL database connection string (optional)
- `CORS_ALLOWED_ORIGINS`: CORS allowed origins (default: `*`)

**Note**: Copy `.env.example` to `.env` and fill in your actual credentials. The `.env` file is gitignored for security.

## System Architecture

### UI/UX Decisions
The application features a modern dark theme with purple accents, a clean sidebar navigation, and a professional dashboard layout built with Bootstrap 5. It includes enhanced alert/notification systems with gradient backgrounds, icons, and improved animations, as well as an enhanced loading overlay. The design is responsive for mobile devices.

### Technical Implementations
- **Backend**: Python 3.11 with Flask 3.1.2.
- **Frontend**: Bootstrap 5 and Vanilla JavaScript for a responsive web interface.
- **AI**: OpenAI GPT-4o-mini (for cost-effectiveness) for story generation, conversational AI, and semantic analysis.
- **Document Processing**: PyPDF2, python-docx, openpyxl, xlrd, and pytesseract for OCR (PNG, JPG, JPEG, GIF, BMP, TIFF) to handle various document types and images.
- **Database**: ChromaDB (vector database) for the AMA feature's knowledge base, utilizing OpenAI embeddings for semantic search.
- **Session Management**: Flask sessions are used for server-side state management.

### Feature Specifications
- **EPIC Ingestion**: Reads EPICs from Jira, including metadata, comments, and attachments.
- **Confluence Integration**: Discovers and crawls linked Confluence documentation recursively, handling pagination.
- **Story Generation**: AI generates user stories with separate developer and QA acceptance criteria.
- **Interactive Interface**: Provides an "Ask Me Anything" (AMA) feature with conversational memory, continuous learning from user feedback, and context retrieval from multiple knowledge sources (Project Knowledge, Conversation Memory, Validated Knowledge).
- **Staging & Export**: A dashboard for reviewing and approving stories before exporting them in JSON or formatted text.
- **Coverage Analysis**: Automatically identifies gaps in EPIC coverage against existing Jira stories/bugs using AI-powered semantic analysis, categorizing requirements as Fully Covered, Partially Covered, or Not Covered, and suggesting new stories.

### System Design Choices
- Modular backend services (Jira, Confluence, AI, Document Processor, Coverage, Vector DB, AMA).
- RESTful API endpoints for all core functionalities.
- Environment variables for sensitive credentials, stored securely in Replit Secrets.
- Temporary files for document processing for security.

## External Dependencies

-   **Jira API**: Used for fetching EPIC details, comments, attachments, and linked issues. Authenticates via email + API token.
-   **Confluence API**: Used for fetching linked documentation pages and their children. Authenticates via email + API token.
-   **OpenAI API**: Provides access to GPT-4o-mini for AI-powered story generation, conversational AI, and semantic analysis.
-   **ChromaDB**: Used as the vector database for the "Ask Me Anything" feature to store and retrieve knowledge.
-   **PyPDF2**: Python library for PDF document processing.
-   **python-docx**: Python library for DOCX document processing.
-   **openpyxl**: Python library for XLSX (Excel) file processing.
-   **xlrd**: Python library for legacy XLS (Excel) file processing.
-   **pytesseract**: Python wrapper for Google's Tesseract-OCR Engine, used for image OCR.