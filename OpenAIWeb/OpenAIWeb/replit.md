# AI Browser Automation CLI

## Overview

This is a Python CLI tool that enables AI-powered browser automation with self-healing code generation capabilities. Users describe automation tasks in natural language, and the tool executes them using OpenAI's GPT-4o-mini and the browser-use library. The tool can generate reusable Playwright scripts from automation sessions and execute them with automatic locator healing when elements change or move on web pages.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Core Architecture Pattern

**Modular Python CLI Application** - The system follows a modular architecture with distinct components for automation execution, code generation, and self-healing capabilities. Each module has a single, well-defined responsibility.

### AI Integration Layer

**OpenAI GPT-4o-mini via browser-use** - The automation engine uses OpenAI's GPT-4o-mini model exclusively (released August 7, 2025) through the browser-use library for intelligent browser automation. This provides natural language task execution without requiring explicit programming.

**Rationale**: Using browser-use abstracts away low-level browser control while providing AI-driven decision making for complex automation scenarios.

### Browser Automation Stack

**Playwright + browser-use** - The system uses Playwright as the underlying browser automation framework, wrapped by browser-use for AI capabilities during initial automation. Generated code uses pure Playwright for execution.

**Chromium Browser Detection** - Automatically detects and uses available Chromium installations from environment variables or common system paths.

**Rationale**: Playwright provides robust, cross-browser automation capabilities with excellent developer experience. Chromium is preferred for consistency across environments.

### Code Generation & Self-Healing System

**Two-Level Recovery Architecture**:
1. **Level 1 - Locator Healing**: When generated Playwright code fails due to changed locators, the AI analyzes the current page and generates new locator strategies
2. **Level 2 - AI Fallback**: If healed locators still fail, browser-use AI takes over to execute the specific action within the same browser session

**Multiple Locator Strategy Pattern** - Generated code includes fallback locator strategies (text, role, label, CSS, XPath) to maximize resilience against page changes.

**Rationale**: Self-healing only applies to generated code execution, not initial automation (which already uses AI natively). This ensures automation reliability even when web pages evolve.

### Module Responsibilities

- **automation_engine.py**: Orchestrates browser-use AI automation and optionally triggers code generation
- **playwright_code_generator.py**: Converts browser-use action history into production-ready Playwright Python scripts
- **self_healing_executor.py**: Executes generated Playwright code with AI-powered locator healing and fallback execution
- **locator_utils.py**: Provides utilities for building robust multi-strategy locators

### CLI Interface

**argparse-based CLI** - Simple command-line interface supporting:
- Direct task execution via natural language
- Code generation with output file specification
- Generated code execution with self-healing
- Headless/headed browser mode toggle
- Verbose logging options

## External Dependencies

### AI Services
- **OpenAI API** (GPT-4o-mini model) - Required for all AI-powered automation and self-healing capabilities. Users must provide their own API key.

### Browser Automation
- **browser-use** - Python library wrapping Playwright with AI capabilities for natural language automation
- **Playwright** - Core browser automation framework for cross-browser testing and automation
- **Chromium** - Browser engine used for automation execution (auto-detected from system)

### Python Dependencies
- **python-dotenv** - Environment variable management for API keys and configuration
- **asyncio** - Asynchronous execution support for browser automation operations

### Browser Extensions (Pre-configured)
The `.config/browseruse/extensions/` directory contains pre-installed browser extensions used during automation:
- **uBlock Origin** (cjpalhdlnbpafiamejdnhcphjbkeiagm) - Ad blocker
- **I don't care about cookies** (edibdbjcniadpccecjdfdjjppcpchdlm) - Cookie consent handler
- **ClearURLs** (lckanjgmijmafbedllaakclkaicjfmnk) - URL tracking parameter remover

**Rationale**: These extensions improve automation reliability by handling common web annoyances (ads, cookie banners, tracking parameters) that could interfere with AI-driven automation.

### Environment
- **Replit** - Primary deployment platform (pre-configured)
- **Python 3.11+** - Minimum required Python version