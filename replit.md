# AI Web Automation Platform

## Overview
An intelligent web automation platform that converts natural language instructions into autonomous browser automation tasks using OpenAI's LLM and Playwright. Users can scrape data, perform assertions, and automate complex browser workflows without writing any code or providing manual selectors.

## Core Features
- **Natural Language Input**: Users describe what they want to automate in plain English
- **Intelligent Element Detection**: AI automatically identifies page elements using Playwright's accessibility tree and auto-locators
- **Autonomous Execution**: System handles navigation, clicking, form filling, and data extraction without explicit selectors
- **Smart Scraping**: Extracts relevant data based on context and user intent
- **Assertion Engine**: Validates page states, element existence, text content, and conditions
- **Real-time Updates**: WebSocket connection streams execution progress to the frontend
- **Error Recovery**: Automatic retry logic for transient failures with fallback strategies
- **Export Capabilities**: Download results as JSON for further processing

## Architecture

### Frontend (React + TypeScript)
- Minimal, functional UI focused on core workflow
- Command input with natural language examples
- Run history sidebar with status indicators
- Execution step viewer with detailed logs and selectors
- Results display for scraped data and assertions
- JSON export functionality
- Real-time updates via WebSocket with auto-reconnection

### Backend (Express + Playwright + OpenAI)
- **LLM Integration**: GPT-5 parses natural language into structured execution plans
- **Playwright Automation**: Executes browser tasks using intelligent element detection
- **Auto-Locators**: Uses getByRole, getByText, getByLabel for reliable element identification
- **Accessibility Tree**: Leverages Playwright's accessibility tree for context-aware automation
- **Error Recovery**: Intelligent retry logic (2s delay + 1 retry) for non-assertion steps
- **Selector Persistence**: Stores resolved selectors for debugging and transparency
- **WebSocket Streaming**: Real-time execution updates for steps, logs, scraped data, and assertions

### Data Models
- **AutomationRun**: Top-level execution container with command, status, timestamps
- **ExecutionStep**: Individual steps (navigate, click, type, extract, assert, wait, screenshot) with results and resolved selectors
- **ScrapedData**: Extracted data in flexible JSON structure
- **AssertionResult**: Validation outcomes with expected vs actual comparisons

## Technology Stack
- **Frontend**: React, TanStack Query, Wouter, Shadcn UI, Tailwind CSS
- **Backend**: Express.js, Playwright, OpenAI GPT-5, WebSockets (ws)
- **Storage**: In-memory (MemStorage) for MVP
- **Real-time**: WebSocket for execution streaming with dedicated message types

## Key Design Decisions
- **No Manual Selectors**: System uses AI + Playwright's intelligent locators exclusively
- **Accessibility-First**: Leverages semantic HTML and ARIA attributes for reliable automation
- **Stateless Execution**: Each run is independent, stored with complete context
- **Streaming Updates**: WebSocket ensures users see progress in real-time (steps, logs, scraped data, assertions)
- **Backend-Focused**: Emphasis on robust automation engine over UI complexity
- **Error Resilience**: Retry logic with proper error clearing prevents stale failure states
- **Developer UX**: Dark theme, monospace for technical data, minimal but functional interface

## API Endpoints
- `POST /api/runs` - Create new automation run (triggers async execution)
- `GET /api/runs` - List all runs
- `GET /api/runs/:id` - Get run details
- `GET /api/runs/:id/steps` - Get execution steps with selectors
- `GET /api/runs/:id/scraped` - Get scraped data
- `GET /api/runs/:id/assertions` - Get assertion results
- WebSocket `/ws` - Real-time execution updates (5 message types)

## WebSocket Message Types
1. `run_status` - Overall run status updates (pending, running, completed, failed)
2. `step_update` - Individual step progress with status and results
3. `scraped_data` - Newly extracted data broadcast immediately
4. `assertion_result` - Assertion outcomes broadcast immediately
5. `log` - Execution logs with levels (info, warn, error)

## Automation Flow
1. User submits natural language command
2. LLM (GPT-5) parses command into structured step plan
3. Orchestrator creates run and steps in storage
4. Playwright executor runs each step sequentially:
   - Uses intelligent locators (no manual selectors)
   - On failure: broadcasts error, waits 2s, retries once (except assertions)
   - On success: persists selector metadata, broadcasts results
   - Extracts/asserts: creates data entities and broadcasts via WebSocket
5. Frontend receives real-time updates and invalidates queries
6. Run completes with all steps, scraped data, and assertion results

## Recent Changes

### 2025-01-20: Complete Implementation
- ✅ Defined complete data schema for automation runs, steps, scraped data, assertions
- ✅ Built minimal functional frontend with command input, run history, and results display
- ✅ Configured design tokens for developer-focused utility application
- ✅ Set up in-memory storage with full CRUD operations
- ✅ Implemented OpenAI GPT-5 LLM planner for natural language parsing
- ✅ Built Playwright executor with intelligent element detection (accessibility tree + auto-locators)
- ✅ Created orchestrator for coordinating LLM + Playwright + WebSocket
- ✅ Added WebSocket server with 5 message types for real-time updates
- ✅ Implemented retry/recovery logic with proper error clearing
- ✅ Fixed selector metadata persistence through storage interface
- ✅ Added real-time streaming for scraped data and assertions
- ✅ Connected frontend to backend APIs with TanStack Query
- ✅ Implemented WebSocket hook with auto-reconnection

## Testing Recommendations
- Test natural language commands: "Go to example.com and click the login button"
- Verify intelligent element detection without manual selectors
- Confirm real-time updates stream correctly for all data types
- Test retry logic by inducing transient failures
- Validate scraping and assertions work end-to-end
- Check concurrent runs respect single-execution guard

## Future Enhancements
- Persistent database (PostgreSQL) for production use
- Multi-step form filling with complex validation
- Screenshot comparison and visual regression testing
- Scheduled automation runs
- API authentication and user management
- Export to CSV in addition to JSON
- Advanced LLM reasoning for dynamic page interactions
- Session persistence across page navigations
