# VisionVault - AI-Powered Browser Automation

## Overview
VisionVault is an AI-powered browser automation tool that converts natural language commands into executable Playwright code. It features automated healing for broken tests, persistent learning capabilities, and intelligent code reuse. The system aims for near 100% success rates in automating browser tasks by leveraging advanced AI planning, multi-strategy healing, and continuous self-learning.

## User Preferences
I want iterative development.
Ask before making major changes.
I prefer detailed explanations.
Do not make changes to the folder `Z`.
Do not make changes to the file `Y`.

## System Architecture

### Core Components
VisionVault is built with Python 3.11, using Flask and Socket.IO for the web server, Playwright for browser automation, and SQLite for data persistence. It integrates OpenAI for AI capabilities and Gemini for semantic search.

- **Web Server (`visionvault/web/app.py`)**: Flask application with Socket.IO for real-time communication.
- **Agents (`visionvault/agents/`)**: Remote execution agents responsible for browser automation and healing.
- **Services (`visionvault/services/`)**: Contains core automation logic including executor, healing, code validation, and vector store.
- **Core (`visionvault/core/`)**: Manages database models and schemas.

### Key Features and AI System
The system incorporates a comprehensive super-intelligent automation system:

1.  **Natural Language to Code**: Converts natural language commands into Playwright scripts.
2.  **Intelligent Pre-Execution Planner**: Analyzes commands using GPT-4o before code generation to predict issues, assess risks, and recommend optimal strategies, generating enhanced prompts for better code quality.
3.  **Intelligent Code Reuse**: Automatically searches for and reuses code and locators from similar existing tasks, applying a three-tier reuse strategy based on similarity to reduce generation time and improve consistency.
4.  **Multi-Strategy Parallel Healing**: When automation fails, it generates and tests 3-4 different fix strategies (locator-based, timing-based, navigation-based, robust-approach) in parallel, selecting the best working solution. GPT-4o is used for enhanced accuracy in healing.
5.  **Continuous Self-Learning Engine**: Records every execution (success/failure) to build a knowledge base, track locator success rates per website, learn automation patterns, and provide recommendations for future tasks.
6.  **Context-Aware Code Generation**: Incorporates insights from the intelligent planner, self-learning engine, and predicted issues to generate resilient, production-ready code with a focus on reliable locators.
7.  **Intelligent Waiting Strategies**: Includes dynamic content detection, SPA awareness, async operation handling, and element stability verification.
8.  **Advanced Error Classification**: Categorizes failures and applies targeted fixes, employing progressive sophistication across healing attempts.
9.  **Automated Healing (Enhanced)**: Utilizes a step-by-step healing process that only retries failed steps, preserving successful ones. It attempts intelligent fixes twice before seeking user intervention. An Advanced Locator Validator tests all possible locator strategies in parallel, automatically selecting the most reliable one.

### UI/UX Decisions
The system prioritizes user experience by reducing unnecessary interruptions through automated AI-driven fixes. It provides clear logging to show which steps failed and how they are being fixed, and visual indicators for reuse status.

### Technical Implementations
-   **Database**: SQLite (`data/automation.db`) for test history, learned tasks, and executions, with a FAISS vector index (`data/vector_index.faiss`) for semantic search using cosine similarity.
-   **Deployment**: Configured as a stateful VM type in Replit, running the server on `0.0.0.0:5000`.
-   **CORS**: Configured for all origins to support Replit's iframe proxy.
-   **Socket.IO**: Uses gevent for asynchronous support.

## External Dependencies

-   **AI**:
    -   **OpenAI**: Used for advanced AI code generation, intelligent pre-execution planning, and enhanced healing (requires `OPENAI_API_KEY`). Specifically, GPT-4o is utilized.
    -   **Google Gemini**: Used for semantic search and vector embeddings (text-embedding-004) (requires `GEMINI_API_KEY`).
-   **Automation Framework**:
    -   **Playwright**: Core browser automation library.
-   **Database**:
    -   **SQLite**: Primary data storage for the application.
    -   **FAISS**: Used for efficient similarity search with vector embeddings.
-   **Web Framework**:
    -   **Flask**: Python web framework.
    -   **Socket.IO**: Enables real-time, bidirectional communication between web clients and the server.