import os
import json
import sqlite3
import uuid
import time
from datetime import datetime
from typing import Optional
from flask import Flask, render_template, request, jsonify, send_from_directory, Response
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from openai import OpenAI
from visionvault.services.executor import ServerExecutor
from visionvault.services.healing_executor import HealingExecutor
from visionvault.services.code_validator import CodeValidator
from visionvault.core.models import Database, LearnedTask, TaskExecution
from visionvault.services.vector_store import SemanticSearch
from visionvault.services.intelligent_planner import IntelligentPlanner
from visionvault.services.self_learning_engine import SelfLearningEngine
from visionvault.services.dom_inspector import dom_inspector
from visionvault.services.mcp_manager import MCPAutomationManager
from visionvault.services.unified_engine import UnifiedAutomationEngine
import base64
import asyncio
import re

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SESSION_SECRET', 'dev-secret-key-change-in-production')
app.config['UPLOAD_FOLDER'] = 'data/uploads'
app.config['DATABASE_PATH'] = 'data/automation.db'
CORS(app)
socketio = SocketIO(
    app, 
    async_mode='threading', 
    cors_allowed_origins="*",
    ping_timeout=60,           # 60 seconds before considering connection dead
    ping_interval=25,          # Send ping every 25 seconds to keep connection alive
    max_http_buffer_size=10**8,  # 100MB buffer for large payloads
    engineio_logger=False,     # Reduce logging overhead
    logger=False
)

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'screenshots'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'logs'), exist_ok=True)

# Cache absolute upload directory path at module load for efficiency
UPLOAD_DIR_ABS = os.path.abspath(app.config['UPLOAD_FOLDER'])

openai_api_key = os.environ.get('OPENAI_API_KEY')
gemini_api_key = os.environ.get('GEMINI_API_KEY')

if openai_api_key:
    client = OpenAI(api_key=openai_api_key)
    print("✅ OpenAI client initialized for code generation")
else:
    client = None
    print("WARNING: OPENAI_API_KEY is not set. AI code generation will not be available.")

if gemini_api_key:
    try:
        semantic_search = SemanticSearch(api_key=gemini_api_key)
        print("✅ Semantic search service initialized with Gemini embeddings")
    except Exception as e:
        semantic_search = None
        print(f"⚠️ Failed to initialize semantic search: {e}")
else:
    semantic_search = None
    print("WARNING: GEMINI_API_KEY is not set. Semantic search will not be available.")

connected_agents = {}
active_healing_executors = {}
active_recorders = {}  # Track active recording sessions
active_loops = {}  # Track event loops for recording sessions

# Initialize database with new tables
db = Database()
print("✅ Database initialized with persistent learning tables")

# Initialize super-intelligent systems
if client:
    intelligent_planner = IntelligentPlanner(openai_client=client)
    print("✅ Intelligent Planner initialized (GPT-4o pre-execution analysis)")
else:
    intelligent_planner = None
    print("⚠️  Intelligent Planner disabled (requires OPENAI_API_KEY)")

self_learning_engine = SelfLearningEngine()
print(f"✅ Self-Learning Engine initialized (learned from {self_learning_engine.knowledge_base['total_executions']} past executions)")

# Initialize MCP automation manager (legacy compatibility)
mcp_manager = MCPAutomationManager(socketio, openai_api_key)
print("✅ MCP Automation Manager initialized")

# Initialize UNIFIED Automation Engine (intelligent merge of MCP + Legacy)
unified_engine = UnifiedAutomationEngine(
    socketio=socketio,
    openai_client=client,
    gemini_api_key=gemini_api_key
)
print("🎯 Unified Automation Engine ready - intelligent strategy selection enabled")


def extract_url_from_command(command: str) -> Optional[str]:
    """Extract URL from natural language command"""
    # Try to find explicit URLs
    url_pattern = r'(https?://[^\s]+|www\.[^\s]+|[a-zA-Z0-9-]+\.(com|org|net|io|dev|co|ai)[^\s]*)'
    urls = re.findall(url_pattern, command.lower())
    
    if urls:
        url = urls[0] if isinstance(urls[0], str) else urls[0][0]
        # Add https:// if missing
        if not url.startswith('http'):
            url = 'https://' + url
        return url
    
    # Try to infer from common patterns
    command_lower = command.lower()
    
    # "go to X" or "navigate to X" or "open X"
    patterns = [
        r'(?:go to|navigate to|open|visit)\s+([a-zA-Z0-9-]+(?:\.[a-zA-Z]{2,})+)',
        r'(?:search on|use)\s+([a-zA-Z0-9-]+)(?:\s|$)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, command_lower)
        if match:
            domain = match.group(1)
            # Common sites without .com/.org etc
            if domain in ['google', 'youtube', 'facebook', 'twitter', 'amazon', 'reddit', 'github', 'linkedin']:
                return f'https://www.{domain}.com'
            elif '.' not in domain:
                return f'https://www.{domain}.com'
            else:
                return f'https://{domain}' if not domain.startswith('http') else domain
    
    return None


def generate_playwright_code(natural_language_command, browser='chromium', similar_tasks=None):
    """
    Generate Playwright code with SUPER-INTELLIGENT analysis and planning.
    
    Uses:
    - Intelligent Planner: Pre-execution analysis and risk assessment
    - Self-Learning Engine: Learned patterns from past executions
    - Similar Task Reuse: Code from related tasks
    
    Args:
        natural_language_command: The user's command
        browser: Browser type (chromium, firefox, webkit)
        similar_tasks: List of similar tasks to use as context (optional)
    """
    if not client:
        raise Exception("OpenAI API key not configured. Please set the OPENAI_API_KEY environment variable.")
    
    try:
        # STEP 0: DOM Inspection - Analyze actual page for perfect locator selection
        dom_analysis = None
        page_url = extract_url_from_command(natural_language_command)
        
        if page_url:
            print(f"\n🔍 INTELLIGENT DOM INSPECTION...")
            print(f"   Analyzing page: {page_url}")
            try:
                # Run DOM inspection in asyncio event loop
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                dom_analysis = loop.run_until_complete(
                    dom_inspector.analyze_page(page_url, natural_language_command)
                )
                loop.close()
                
                if 'error' not in dom_analysis:
                    intent_matched = len(dom_analysis.get('intent_matched_elements', []))
                    form_elements = len(dom_analysis.get('form_elements', []))
                    interactive = len(dom_analysis.get('interactive_elements', []))
                    print(f"   ✅ Page analyzed successfully!")
                    print(f"   Found: {intent_matched} intent-matched, {form_elements} form, {interactive} interactive elements")
                else:
                    print(f"   ⚠️  DOM inspection failed: {dom_analysis.get('error', 'Unknown error')}")
                    print(f"   Falling back to standard locator strategies")
                    dom_analysis = None
            except Exception as e:
                print(f"   ⚠️  DOM inspection error: {str(e)}")
                print(f"   Falling back to standard locator strategies")
                dom_analysis = None
        else:
            print("\n⚠️  No URL detected in command - skipping DOM inspection")
        
        # STEP 1: Pre-execution intelligent planning
        execution_plan = None
        learned_recommendations = None
        
        if intelligent_planner:
            print("\n🧠 INTELLIGENT PRE-EXECUTION ANALYSIS...")
            execution_plan = intelligent_planner.analyze_command(natural_language_command)
            print(f"   Intent: {execution_plan['intent']}")
            print(f"   Complexity: {execution_plan['complexity']}")
            print(f"   Confidence: {execution_plan['confidence_score']:.0f}%")
            print(f"   Predicted issues: {len(execution_plan['potential_issues'])}")
            print(f"   Recommended strategies: {len(execution_plan['recommended_strategies'])}")
        
        # STEP 2: Get self-learning recommendations
        learned_recommendations = self_learning_engine.get_recommendations(natural_language_command)
        print(f"\n📚 SELF-LEARNING RECOMMENDATIONS:")
        print(f"   Predicted success rate: {learned_recommendations['predicted_success_rate']:.1f}%")
        print(f"   Recommended locators: {', '.join(learned_recommendations['recommended_locators'][:3])}")
        print(f"   Confidence: {learned_recommendations['confidence']:.0f}%")
        # Build system prompt with reusable code context
        system_prompt = """You are an expert at converting natural language commands into Playwright Python code with ENHANCED RELIABILITY.

Your goal is to generate code efficiently by REUSING existing code and locators whenever possible.

Generate complete, executable Playwright code that:
1. Uses async/await syntax
2. Includes proper browser launch with the specified browser
3. Has error handling with proper cleanup
4. Returns a dict with 'success', 'logs', 'screenshot', and 'current_step' keys
5. ALWAYS takes screenshot BEFORE closing browser (CRITICAL)
6. The code should be a complete async function named 'run_test' that takes browser_name and headless parameters

CRITICAL TIMEOUT RULES:
- Use 5000ms (5 seconds) timeout for LOCATOR action methods only
- LOCATOR actions that accept timeout: click(), fill(), locator.press(), select_option(), check(), etc.
- NEVER add timeout to: locator() calls, page.keyboard.press(), page.mouse methods
- Examples:
  ✅ CORRECT: await page.get_by_role("button").click(timeout=5000)
  ✅ CORRECT: await page.get_by_placeholder("Search").fill("text", timeout=5000)
  ✅ CORRECT: await page.get_by_text("Enter").press("Enter", timeout=5000)  # locator.press()
  ✅ CORRECT: await page.keyboard.press("Enter")  # NO timeout parameter!
  ❌ WRONG: await page.locator("button", timeout=5000)  # locator() doesn't accept timeout!
  ❌ WRONG: await page.keyboard.press("Enter", timeout=5000)  # keyboard.press() doesn't accept timeout!

CRITICAL STEP TRACKING:
- Label each major step with a comment like "# STEP 1: Navigate to website"
- Update current_step variable before each step for granular error tracking
- Log each step completion with step number

CRITICAL LOCATOR SELECTION STRATEGY (Priority Order - Use the FIRST available):
Based on Playwright best practices and proven success rates, ALWAYS select locators in this priority order:

⚠️ CRITICAL RULE: NEVER use CSS selectors or page.locator() unless absolutely necessary!
❌ BAD: page.locator("input[aria-label='Search']") or page.locator("#id") 
✅ GOOD: page.get_by_role(), page.get_by_placeholder(), page.get_by_label()

1. Test ID (HIGHEST PRIORITY - 99% success rate)
   ✅ page.get_by_test_id("submit-btn")
   Use when element has data-testid attribute

2. Role with Name (Accessibility-first - 95% success rate) ⭐ PREFERRED
   ✅ page.get_by_role("button", name="Submit")
   ✅ page.get_by_role("link", name="Login")
   ✅ page.get_by_role("textbox", name="Search")
   ✅ page.get_by_role("combobox", name="Search")  # For search boxes!
   Common roles: button, link, textbox, combobox, checkbox, radio, heading
   ALWAYS use for interactive elements (buttons, links, inputs)

3. Placeholder (90% success rate)
   ✅ page.get_by_placeholder("Enter your email")
   ✅ page.get_by_placeholder("Search")
   Use for form inputs with placeholder text

4. Label (85% success rate)
   ✅ page.get_by_label("Email Address")
   Use when form field has associated label

5. Text Content (80% success rate)
   ✅ page.get_by_text("Submit", exact=True)
   Use for elements with unique visible text

6. Alt Text (for images only)
   ✅ page.get_by_alt_text("Company Logo")

7. Title Attribute
   ✅ page.get_by_title("Close dialog")

8. ❌ CSS Selectors (LAST RESORT - 70% success rate, often breaks)
   Only if NO semantic locator exists:
   page.locator("#unique-id")  # ID only
   ❌ NEVER use: page.locator("input"), page.locator(".class"), page.locator("[aria-label='...']")

SMART LOCATOR SELECTION BY ELEMENT TYPE:
┌─────────────────┬────────────────────────────────────────────────┐
│ Element Type    │ Best Locator (in order of preference)          │
├─────────────────┼────────────────────────────────────────────────┤
│ Search box      │ 1. get_by_role("combobox", name="Search")     │
│                 │ 2. get_by_placeholder("Search...")             │
│                 │ 3. get_by_label("Search")                      │
├─────────────────┼────────────────────────────────────────────────┤
│ Button          │ 1. get_by_role("button", name="Submit")       │
│                 │ 2. get_by_text("Submit", exact=True)           │
├─────────────────┼────────────────────────────────────────────────┤
│ Link            │ 1. get_by_role("link", name="Login")          │
│                 │ 2. get_by_text("Login", exact=True)            │
├─────────────────┼────────────────────────────────────────────────┤
│ Text input      │ 1. get_by_label("Email")                      │
│                 │ 2. get_by_placeholder("Enter email")           │
│                 │ 3. get_by_role("textbox", name="Email")       │
├─────────────────┼────────────────────────────────────────────────┤
│ Checkbox/Radio  │ 1. get_by_role("checkbox", name="Remember")   │
│                 │ 2. get_by_label("Remember me")                 │
└─────────────────┴────────────────────────────────────────────────┘

CRITICAL: Search boxes are usually role="combobox" or have a placeholder!
Example: Google search → page.get_by_role("combobox", name="Search") or page.get_by_placeholder("Search")

CRITICAL NAVIGATION RULES:
- NEVER use page.wait_for_navigation() - this is Puppeteer syntax, NOT Playwright!
- For navigation after click/submit, use: async with page.expect_navigation(): await page.click(...)
- Or use: await page.wait_for_load_state('networkidle') after the action
- Or simply await page.click() and Playwright auto-waits for navigation
- Example: await page.get_by_role("button", name="Submit").click(timeout=5000)
          await page.wait_for_load_state('networkidle')  # Wait for page to load

CRITICAL RULE: Always take screenshot BEFORE closing browser/page. Never close browser before screenshot.

Example structure with BEST PRACTICE LOCATORS:
async def run_test(browser_name='chromium', headless=True):
    from playwright.async_api import async_playwright
    logs = []
    screenshot = None
    browser = None
    page = None
    current_step = 0
    
    try:
        async with async_playwright() as p:
            browser = await getattr(p, browser_name).launch(headless=headless)
            page = await browser.new_page()
            
            # STEP 1: Navigate to website
            current_step = 1
            await page.goto('https://example.com', timeout=10000)
            logs.append("STEP 1: Navigated to website")
            
            # STEP 2: Click login button (using role - Score 100)
            current_step = 2
            await page.get_by_role("button", name="Login").click(timeout=5000)
            logs.append("STEP 2: Clicked login button")
            
            # STEP 3: Fill username (using label - Score 140)
            current_step = 3
            await page.get_by_label("Username").fill('testuser', timeout=5000)
            logs.append("STEP 3: Filled username")
            
            # STEP 4: Fill password (using placeholder - Score 120)
            current_step = 4
            await page.get_by_placeholder("Enter password").fill('pass123', timeout=5000)
            logs.append("STEP 4: Filled password")
            
            # STEP 5: Submit (using role - Score 100)
            current_step = 5
            await page.get_by_role("button", name="Submit").click(timeout=5000)
            logs.append("STEP 5: Submitted form")
            
            # CRITICAL: Screenshot and page HTML capture BEFORE closing
            screenshot = await page.screenshot()
            page_html = await page.content()  # Capture page HTML for healing analysis
            await browser.close()
            return {'success': True, 'logs': logs, 'screenshot': screenshot, 'page_html': page_html, 'current_step': current_step}
    except Exception as e:
        error_msg = f"Error at STEP {current_step}: {str(e)}"
        logs.append(error_msg)
        # Try to get screenshot and page HTML even on error, BEFORE cleanup
        page_html = ''
        if page:
            try:
                screenshot = await page.screenshot()
                page_html = await page.content()  # Capture page HTML for healing analysis
            except:
                pass
        if browser:
            try:
                await browser.close()
            except:
                pass
        return {'success': False, 'logs': logs, 'screenshot': screenshot, 'page_html': page_html, 'current_step': current_step}

Only return the function code, no explanations."""

        # Add DOM inspection results to the prompt (HIGHEST PRIORITY - real page data!)
        if dom_analysis and 'error' not in dom_analysis:
            dom_recommendations = dom_inspector.generate_locator_recommendations(dom_analysis)
            system_prompt += f"\n\n{dom_recommendations}\n"
            system_prompt += "🎯 CRITICAL: Use the exact locators from DOM analysis above - they are CONFIRMED to exist!\n"
            system_prompt += "These locators were extracted from the actual live page, ensuring 99%+ accuracy.\n\n"

        # Add intelligent planner's recommendations to the prompt
        if execution_plan:
            system_prompt += f"\n\n--- INTELLIGENT EXECUTION PLAN ---\n"
            system_prompt += f"Intent: {execution_plan['intent']}\n"
            system_prompt += f"Complexity: {execution_plan['complexity']}\n"
            system_prompt += f"Estimated Time: {execution_plan['estimated_time']}\n\n"
            
            if execution_plan['potential_issues']:
                system_prompt += "PREDICTED POTENTIAL ISSUES (must handle):\n"
                for issue in execution_plan['potential_issues']:
                    system_prompt += f"- {issue}\n"
                system_prompt += "\n"
            
            if execution_plan['recommended_strategies']:
                system_prompt += "REQUIRED STRATEGIES (must implement):\n"
                for strategy in execution_plan['recommended_strategies']:
                    system_prompt += f"- {strategy}\n"
                system_prompt += "\n"
        
        # Add self-learning recommendations
        if learned_recommendations['recommended_locators']:
            system_prompt += f"\n--- LEARNED BEST LOCATORS ---\n"
            system_prompt += f"Based on {self_learning_engine.knowledge_base['total_executions']} past executions:\n"
            for loc in learned_recommendations['recommended_locators'][:5]:
                system_prompt += f"- {loc} (proven effective)\n"
            system_prompt += "\n"
        
        # Add similar tasks as context if available - ENHANCED CODE ADAPTATION MODE
        if similar_tasks and len(similar_tasks) > 0:
            best_similarity = similar_tasks[0].get('similarity_score', 0)
            
            system_prompt += "\n\n--- 🎯 SMART CODE ADAPTATION MODE ACTIVATED ---\n"
            system_prompt += "Below are existing tasks that are similar to the new request. Your job is to INTELLIGENTLY ADAPT the existing code, NOT generate from scratch.\n\n"
            
            for i, task in enumerate(similar_tasks, 1):
                similarity = task.get('similarity_score', 0)
                system_prompt += f"Task {i} (Similarity: {similarity:.0%}): {task['task_name']}\n"
                if task.get('description'):
                    system_prompt += f"Description: {task['description']}\n"
                system_prompt += f"Existing Code:\n```python\n{task['playwright_code']}\n```\n\n"
            
            # Add smart adaptation instructions based on similarity level
            if best_similarity > 0.50:
                # High similarity - minor adaptation needed
                system_prompt += """--- 🔧 CODE ADAPTATION STRATEGY (HIGH SIMILARITY) ---
⚠️  WARNING: The existing task is VERY similar to the new request!

MANDATORY APPROACH - Follow these steps EXACTLY:
1. START with the existing code from Task 1 as your BASE
2. IDENTIFY what needs to change (e.g., search terms, URLs, button names)
3. REPLACE only the specific values that differ - DO NOT rewrite locators or structure
4. KEEP all working locators, selectors, and navigation patterns UNCHANGED
5. MAINTAIN the exact same code structure and error handling

EXAMPLES OF SMART ADAPTATION:
- Old: await page.fill("#search", "dog food")
  New: await page.fill("#search", "cat food")  ← ONLY change the search term
  
- Old: await page.goto("https://flipkart.com")
  New: await page.goto("https://flipkart.com")  ← KEEP if same site
  
- Old: await page.get_by_role("button", name="Search").click()
  New: await page.get_by_role("button", name="Search").click()  ← KEEP if same button

❌ DO NOT:
- Generate new code from scratch
- Change working locators or selectors
- Modify the overall structure
- Add unnecessary waits or steps

✅ DO:
- Copy the existing code structure
- Replace ONLY the parameter values that need to change
- Preserve all proven locators and patterns
- Keep comments and logging intact
"""
            else:
                # Moderate similarity - partial reuse
                system_prompt += """--- 🔧 CODE ADAPTATION STRATEGY (MODERATE SIMILARITY) ---
The existing tasks share some patterns with the new request.

RECOMMENDED APPROACH:
1. Identify REUSABLE patterns: URLs, navigation flows, locator types, wait strategies
2. COPY working code sections (navigation, form filling, button clicks)
3. ADAPT values and targets to match the new requirement
4. COMBINE patterns from multiple tasks if needed
5. Only generate NEW code for unique parts not covered

FOCUS ON:
- Reusing proven locators and selectors
- Maintaining the same navigation structure
- Copying error handling patterns
- Adapting values (search terms, form data) to new requirements
"""
            
            system_prompt += "\n🎯 GOAL: Generate adapted code that leverages existing proven patterns and minimizes new code generation.\n"

        # Build enhanced user prompt with all context
        user_prompt = f"NEW REQUEST: {natural_language_command}\n"
        user_prompt += f"Target Browser: {browser}\n"
        
        if similar_tasks and len(similar_tasks) > 0:
            best_similarity = similar_tasks[0].get('similarity_score', 0)
            if best_similarity > 0.50:
                user_prompt += f"\n⚠️  CRITICAL: An existing task is {best_similarity:.0%} similar to this request!\n"
                user_prompt += "You MUST adapt the existing code, NOT generate from scratch.\n"
                user_prompt += "Identify the differences and make MINIMAL changes to the existing code.\n"
            else:
                user_prompt += f"\n✅ Found {len(similar_tasks)} related task(s). Reuse their proven patterns and locators.\n"
        
        if execution_plan:
            user_prompt += f"\n\nEXECUTION PLAN: {execution_plan['full_analysis'][:500]}"
        
        user_prompt += f"\n\nGenerate PRODUCTION-READY code that handles all predicted issues and implements all recommended strategies."

        # Use GPT-4o-mini for code generation
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2  # Lower temperature for more consistent, reliable code
        )

        code = response.choices[0].message.content
        if not code:
            raise Exception("No code generated from OpenAI")
        code = code.strip()
        if code.startswith('```python'):
            code = code[9:]
        if code.startswith('```'):
            code = code[3:]
        if code.endswith('```'):
            code = code[:-3]

        return code.strip()
    except Exception as e:
        raise Exception(f"OpenAI API error: {str(e)}")


def generate_playwright_code_from_recording(recorded_events):
    """
    Convert recorded events from ComprehensiveRecordingSessionManager to executable Playwright code.
    This generates proper Playwright code with full browser launch, error handling, and screenshot capture.
    """
    if not recorded_events or len(recorded_events) == 0:
        raise Exception("No recorded events to convert to code")
    
    # Start building the code
    code_lines = [
        "async def run_test(browser_name='chromium', headless=True):",
        "    from playwright.async_api import async_playwright",
        "    logs = []",
        "    screenshot = None",
        "    browser = None",
        "    page = None",
        "    ",
        "    try:",
        "        async with async_playwright() as p:",
        "            browser = await getattr(p, browser_name).launch(headless=headless)",
        "            page = await browser.new_page()",
        "            ",
    ]
    
    # Convert each event to Playwright code
    for i, event in enumerate(recorded_events):
        action = event.get('action')
        target = event.get('target', '')
        value = event.get('value', '')
        description = event.get('description', '')
        attributes = event.get('attributes', {})
        
        # Escape single quotes in strings
        if value:
            value = str(value).replace("'", "\\'")
        if target:
            target = str(target).replace("'", "\\'")
        
        if action == 'navigation':
            # Navigation action
            code_lines.append(f"            await page.goto('{target}')")
            code_lines.append(f"            logs.append('Navigated to {target}')")
            
        elif action == 'click':
            # Check if next event is navigation (click causes page change)
            next_event = recorded_events[i + 1] if i + 1 < len(recorded_events) else None
            is_link = attributes.get('tag') == 'a'
            is_form_submit = attributes.get('type') == 'submit' or attributes.get('isFormSubmit')
            causes_navigation = (next_event and next_event.get('action') == 'navigation')
            
            # If click causes navigation, use expect_navigation
            if causes_navigation or is_link or is_form_submit:
                code_lines.append(f"            # Click that triggers navigation")
                code_lines.append(f"            async with page.expect_navigation():")
                code_lines.append(f"                await page.click('{target}')")
                code_lines.append(f"            logs.append('Clicked {target} and navigated')")
            else:
                # Regular click without navigation
                code_lines.append(f"            await page.click('{target}')")
                code_lines.append(f"            logs.append('Clicked {target}')")
            
        elif action == 'type':
            # Input/fill action
            code_lines.append(f"            await page.fill('{target}', '{value}')")
            code_lines.append(f"            logs.append('Typed into {target}')")
            
        elif action == 'change':
            # Change action (select, checkbox, radio)
            attributes = event.get('attributes', {})
            tag = attributes.get('tag', 'unknown')
            
            if tag == 'select':
                code_lines.append(f"            await page.select_option('{target}', '{value}')")
                code_lines.append(f"            logs.append('Selected option {value} in {target}')")
            elif attributes.get('type') in ['checkbox', 'radio']:
                if value:  # If checked
                    code_lines.append(f"            await page.check('{target}')")
                    code_lines.append(f"            logs.append('Checked {target}')")
                else:
                    code_lines.append(f"            await page.uncheck('{target}')")
                    code_lines.append(f"            logs.append('Unchecked {target}')")
            else:
                code_lines.append(f"            await page.fill('{target}', '{value}')")
                code_lines.append(f"            logs.append('Changed {target} to {value}')")
                
        elif action == 'keypress':
            # Key press action
            key = event.get('key', 'Enter')
            code_lines.append(f"            await page.keyboard.press('{key}')")
            code_lines.append(f"            logs.append('Pressed {key} key')")
            
        elif action == 'dialog':
            # Dialog detection (alert, confirm, prompt)
            dialog_type = event.get('dialog_type', 'alert')
            dialog_message = event.get('target', '').replace("'", "\\'")
            code_lines.append(f"            # Handle {dialog_type} dialog")
            code_lines.append(f"            # Dialog will auto-accept in Playwright")
            code_lines.append(f"            logs.append('Dialog appeared: {dialog_message}')")
        
        elif action == 'dialog_accept':
            # Dialog acceptance
            dialog_type = event.get('target', 'dialog')
            code_lines.append(f"            logs.append('Accepted {dialog_type}')")
        
        elif action == 'popup_opened':
            # New window/popup opened
            popup_url = target.replace("'", "\\'") if target else 'popup'
            code_lines.append(f"            # New popup window opened")
            code_lines.append(f"            # Playwright automatically tracks popup pages")
            code_lines.append(f"            logs.append('Popup opened: {popup_url}')")
        
        elif action == 'page_created':
            # New tab created
            page_url = target.replace("'", "\\'") if target else 'new page'
            code_lines.append(f"            # New page/tab opened")
            code_lines.append(f"            logs.append('New page opened: {page_url}')")
        
        elif action == 'frame_attached':
            # iFrame/widget loaded
            frame_name = event.get('frame_name', 'widget')
            code_lines.append(f"            # Frame/Widget loaded: {frame_name}")
            code_lines.append(f"            logs.append('Frame attached: {frame_name}')")
            
        elif action == 'form_submit':
            # Form submission - press Enter on the form
            code_lines.append(f"            await page.keyboard.press('Enter')")
            code_lines.append(f"            logs.append('Submitted form')")
    
    code_lines.extend([
        "            ",
        "            # Take screenshot before closing",
        "            screenshot = await page.screenshot()",
        "            logs.append('Screenshot captured')",
        "            ",
        "            await browser.close()",
        "            return {'success': True, 'logs': logs, 'screenshot': screenshot}",
        "    ",
        "    except Exception as e:",
        "        logs.append(f'Error: {str(e)}')",
        "        if 'page' in locals():",
        "            try:",
        "                screenshot = await page.screenshot()",
        "            except:",
        "                pass",
        "        if 'browser' in locals():",
        "            try:",
        "                await browser.close()",
        "            except:",
        "                pass",
        "        return {'success': False, 'logs': logs, 'screenshot': screenshot}"
    ])
    
    return "\n".join(code_lines)


@app.after_request
def add_header(response):
    """Add cache-control headers to prevent caching issues in iframe"""
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/history')
def get_history():
    conn = sqlite3.connect(app.config['DATABASE_PATH'])
    c = conn.cursor()
    c.execute('SELECT * FROM test_history ORDER BY created_at DESC LIMIT 50')
    rows = c.fetchall()
    conn.close()
    
    history = []
    for row in rows:
        history.append({
            'id': row[0],
            'command': row[1],
            'generated_code': row[2],
            'healed_code': row[3],
            'browser': row[4],
            'mode': row[5],
            'execution_location': row[6],
            'status': row[7],
            'logs': row[8],
            'screenshot_path': row[9],
            'created_at': row[10]
        })
    
    return jsonify(history)

@app.route('/api/history/<int:history_id>', methods=['DELETE'])
def delete_history_item(history_id):
    """Delete a single history item."""
    try:
        conn = sqlite3.connect(app.config['DATABASE_PATH'])
        c = conn.cursor()
        c.execute('DELETE FROM test_history WHERE id=?', (history_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'History item deleted'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/history/all', methods=['DELETE'])
def delete_all_history():
    """Delete all history items."""
    try:
        conn = sqlite3.connect(app.config['DATABASE_PATH'])
        c = conn.cursor()
        c.execute('DELETE FROM test_history')
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'All history deleted'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/history/rerun/<int:history_id>', methods=['POST'])
def rerun_from_history(history_id):
    """Re-execute a test from history using healed code if available, otherwise generated code."""
    try:
        data = request.json or {}
        
        conn = sqlite3.connect(app.config['DATABASE_PATH'])
        c = conn.cursor()
        c.execute('SELECT command, generated_code, healed_code, browser, mode, execution_location FROM test_history WHERE id=?', (history_id,))
        row = c.fetchone()
        conn.close()
        
        if not row:
            return jsonify({'error': 'History item not found'}), 404
        
        command, generated_code, healed_code, browser, mode, execution_location = row
        
        code_to_use = healed_code if healed_code else generated_code
        code_source = 'healed' if healed_code else 'generated'
        
        use_healing = data.get('use_healing', True)
        auto_save = data.get('auto_save', False)
        
        conn = sqlite3.connect(app.config['DATABASE_PATH'])
        c = conn.cursor()
        c.execute('INSERT INTO test_history (command, generated_code, healed_code, browser, mode, execution_location, status) VALUES (?, ?, ?, ?, ?, ?, ?)',
                  (command, generated_code, healed_code, browser, mode, execution_location, 'pending'))
        test_id = c.lastrowid
        conn.commit()
        conn.close()
        
        print(f"🔄 Re-running test from history #{history_id} as test #{test_id}")
        print(f"   Using {code_source} code")
        print(f"   Command: {command}")
        
        if execution_location == 'server':
            if use_healing:
                socketio.start_background_task(execute_with_healing, test_id, code_to_use, browser, mode, auto_save=auto_save, original_command=command)
            else:
                socketio.start_background_task(execute_on_server, test_id, code_to_use, browser, mode, auto_save=auto_save, original_command=command)
        else:
            agent_sid = None
            for sid in connected_agents:
                agent_sid = sid
                break
            
            if use_healing:
                socketio.start_background_task(execute_agent_with_healing, test_id, code_to_use, browser, mode, auto_save=auto_save, original_command=command)
            else:
                if agent_sid:
                    socketio.emit('execute_on_agent', {
                        'test_id': test_id,
                        'code': code_to_use,
                        'browser': browser,
                        'mode': mode
                    }, to=agent_sid)
                else:
                    return jsonify({'error': 'No agent connected'}), 503
        
        return jsonify({
            'test_id': test_id,
            'code': code_to_use,
            'code_source': code_source,
            'original_history_id': history_id,
            'command': command
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/execute', methods=['POST'])
def execute_test():
    """
    UNIFIED AUTOMATION ENDPOINT
    Intelligently routes to MCP or Code Generation based on task analysis.
    No more manual engine selection - the system decides!
    """
    data = request.json or {}
    command = data.get('command')
    browser = data.get('browser', 'chromium')
    mode = data.get('mode', 'headless')
    execution_location = data.get('execution_location', 'server')
    use_healing = data.get('use_healing', True)
    auto_save = data.get('auto_save', False)
    
    # Backward compatibility: accept automation_engine but ignore it
    # The unified engine will make its own intelligent decision
    _ = data.get('automation_engine', None)  # Ignored
    
    if not command:
        return jsonify({'error': 'Command is required'}), 400
    
    # Server execution only for now (agent execution maintained for compatibility)
    if execution_location != 'server':
        # Fall back to legacy agent execution
        return _execute_legacy_agent(command, browser, mode, use_healing, auto_save)
    
    try:
        print(f"\n🎯 UNIFIED AUTOMATION ENGINE")
        print(f"   Command: {command}")
        print(f"   Browser: {browser}, Mode: {mode}")
        
        headless = mode == 'headless'
        
        # Create test history entry
        conn = sqlite3.connect(app.config['DATABASE_PATH'])
        c = conn.cursor()
        c.execute('INSERT INTO test_history (command, generated_code, browser, mode, execution_location, status) VALUES (?, ?, ?, ?, ?, ?)',
                  (command, '[Unified Engine - Analyzing...]', browser, mode, 'server', 'pending'))
        test_id = c.lastrowid
        conn.commit()
        conn.close()
        
        # Execute with unified engine in background
        def run_unified_automation():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    unified_engine.execute(test_id, command, browser, headless)
                )
                
                # Emit final result
                socketio.emit('execution_result', {
                    'test_id': test_id,
                    'success': result['success'],
                    'logs': result['logs'],
                    'screenshot': result.get('screenshot'),
                    'code': result.get('code')
                })
                
                # Update database with final code and results
                conn = sqlite3.connect(app.config['DATABASE_PATH'])
                c = conn.cursor()
                
                final_code = result.get('code') or '[Unified Engine Execution]'
                screenshot_path = None
                
                if result.get('screenshot'):
                    screenshot_path = f"screenshots/unified_{test_id}.png"
                    screenshot_full_path = os.path.join(app.config['UPLOAD_FOLDER'], screenshot_path)
                    os.makedirs(os.path.dirname(screenshot_full_path), exist_ok=True)
                    with open(screenshot_full_path, 'wb') as f:
                        f.write(base64.b64decode(result['screenshot']))
                
                c.execute('UPDATE test_history SET status = ?, logs = ?, screenshot_path = ?, generated_code = ? WHERE id = ?',
                          ('success' if result['success'] else 'failed',
                           json.dumps(result['logs']),
                           screenshot_path,
                           final_code,
                           test_id))
                conn.commit()
                conn.close()
                
            except Exception as e:
                import traceback
                traceback.print_exc()
                
                # Emit error
                socketio.emit('execution_result', {
                    'test_id': test_id,
                    'success': False,
                    'logs': [f"❌ Execution error: {str(e)}"],
                    'screenshot': None,
                    'code': None
                })
                
                # Update database with error
                conn = sqlite3.connect(app.config['DATABASE_PATH'])
                c = conn.cursor()
                c.execute('UPDATE test_history SET status = ?, logs = ? WHERE id = ?',
                          ('failed', json.dumps([f"Error: {str(e)}"]), test_id))
                conn.commit()
                conn.close()
            finally:
                loop.close()
        
        socketio.start_background_task(run_unified_automation)
        
        return jsonify({
            'test_id': test_id,
            'code': '[Unified Engine - Strategy will be selected automatically]',
            'code_source': 'unified',
            'automation_engine': 'unified'
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Unified automation failed: {str(e)}'}), 500


def _execute_legacy_agent(command, browser, mode, use_healing, auto_save):
    """Legacy agent execution path (for backward compatibility)"""
    try:
        # Generate code using legacy method
        generated_code = generate_playwright_code(command, browser)
        
        validator = CodeValidator()
        if not validator.validate(generated_code):
            error_msg = "Code failed security validation: " + "; ".join(validator.get_errors())
            return jsonify({'error': error_msg}), 400
        
        conn = sqlite3.connect(app.config['DATABASE_PATH'])
        c = conn.cursor()
        c.execute('INSERT INTO test_history (command, generated_code, browser, mode, execution_location, status) VALUES (?, ?, ?, ?, ?, ?)',
                  (command, generated_code, browser, mode, 'agent', 'pending'))
        test_id = c.lastrowid
        conn.commit()
        conn.close()
        
        # Agent execution
        agent_sid = None
        for sid in connected_agents:
            agent_sid = sid
            break
        
        if use_healing:
            socketio.start_background_task(execute_agent_with_healing, test_id, generated_code, browser, mode, auto_save=auto_save, original_command=command)
        else:
            if agent_sid:
                socketio.emit('execute_on_agent', {
                    'test_id': test_id,
                    'code': generated_code,
                    'browser': browser,
                    'mode': mode
                }, to=agent_sid)
            else:
                return jsonify({'error': 'No agent connected'}), 503
        
        return jsonify({
            'test_id': test_id,
            'code': generated_code,
            'code_source': 'generated'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def execute_on_server(test_id, code, browser, mode, auto_save=False, original_command=None):
    executor = ServerExecutor()
    headless = mode == 'headless'
    
    socketio.emit('execution_status', {
        'test_id': test_id,
        'status': 'running',
        'message': f'Executing on server in {mode} mode...'
    })
    
    result = executor.execute(code, browser, headless)
    
    screenshot_path = None
    if result.get('screenshot'):
        screenshot_path = f"screenshots/test_{test_id}.png"
        with open(os.path.join(app.config['UPLOAD_FOLDER'], screenshot_path), 'wb') as f:
            f.write(result['screenshot'])
    
    logs_json = json.dumps(result.get('logs', [])) if result.get('logs') else '[]'
    status = 'success' if result.get('success') else 'failed'
    code = code if code else 'No code generated.'

    conn = sqlite3.connect(app.config['DATABASE_PATH'])
    c = conn.cursor()
    c.execute('UPDATE test_history SET status=?, logs=?, screenshot_path=? WHERE id=?',
              (status, logs_json, screenshot_path, test_id))
    conn.commit()
    conn.close()
    
    # Auto-save successful executions as learned tasks
    if auto_save and result.get('success') and original_command and semantic_search:
        try:
            task_id = str(uuid.uuid4())
            task_name = original_command[:100]  # Limit name length
            
            task = LearnedTask(
                task_id=task_id,
                task_name=task_name,
                playwright_code=code,
                description=f"Auto-saved from successful execution in {mode} mode",
                steps=[],
                tags=[mode, browser, 'auto-saved']
            )
            task.save()
            
            # Index for semantic search
            semantic_search.index_task(task)
            print(f"✅ Auto-saved successful execution as learned task: '{task_name}'")
            
            socketio.emit('task_auto_saved', {
                'test_id': test_id,
                'task_id': task_id,
                'task_name': task_name
            })
        except Exception as e:
            print(f"⚠️  Failed to auto-save task: {e}")
    
    # SELF-LEARNING: Record execution for continuous improvement
    if original_command:
        self_learning_engine.learn_from_execution(
            command=original_command,
            code=code,
            result=result,
            healing_attempts=0,
            url=''
        )
    
    socketio.emit('execution_complete', {
        'test_id': test_id,
        'status': status,
        'logs': result.get('logs', []),
        'screenshot_path': screenshot_path
    })

def execute_with_healing(test_id, code, browser, mode, auto_save=False, original_command=None):
    healing_executor = HealingExecutor(socketio, api_key=openai_api_key)
    active_healing_executors[test_id] = healing_executor
    headless = mode == 'headless'
    
    socketio.emit('execution_status', {
        'test_id': test_id,
        'status': 'running',
        'message': f'Executing with healing in {mode} mode...'
    })
    
    try:
        result = asyncio.run(healing_executor.execute_with_healing(code, browser, headless, test_id))
    finally:
        if test_id in active_healing_executors:
            del active_healing_executors[test_id]
    
    screenshot_path = None
    if result.get('screenshot'):
        screenshot_path = f"screenshots/test_{test_id}.png"
        with open(os.path.join(app.config['UPLOAD_FOLDER'], screenshot_path), 'wb') as f:
            f.write(result['screenshot'])
    
    logs_json = json.dumps(result.get('logs', [])) if result.get('logs') else '[]'
    status = 'success' if result.get('success') else 'failed'
    healed_code = result.get('healed_script')
    
    print(f"\n💾 SAVING TO DATABASE:")
    print(f"  test_id: {test_id}")
    print(f"  status: {status}")
    print(f"  healed_code is None: {healed_code is None}")
    print(f"  healed_code length: {len(healed_code) if healed_code else 0}", flush=True)
    
    conn = sqlite3.connect(app.config['DATABASE_PATH'])
    c = conn.cursor()
    c.execute('UPDATE test_history SET status=?, logs=?, screenshot_path=?, healed_code=? WHERE id=?',
              (status, logs_json, screenshot_path, healed_code, test_id))
    conn.commit()
    conn.close()
    
    print(f"  ✅ Database updated successfully", flush=True)
    
    # Auto-save successful healed executions as learned tasks
    if auto_save and result.get('success') and original_command and semantic_search:
        try:
            # Use healed code if available, otherwise use original code
            final_code = healed_code if healed_code else code
            task_id = str(uuid.uuid4())
            task_name = original_command[:100]  # Limit name length
            
            task = LearnedTask(
                task_id=task_id,
                task_name=task_name,
                playwright_code=final_code,
                description=f"Auto-saved from successful {'healed' if healed_code else 'execution'} in {mode} mode",
                steps=[],
                tags=[mode, browser, 'auto-saved', 'healed' if healed_code else 'standard']
            )
            task.save()
            
            # Index for semantic search
            semantic_search.index_task(task)
            print(f"✅ Auto-saved successful {'healed ' if healed_code else ''}execution as learned task: '{task_name}'")
            
            socketio.emit('task_auto_saved', {
                'test_id': test_id,
                'task_id': task_id,
                'task_name': task_name,
                'was_healed': bool(healed_code)
            })
        except Exception as e:
            print(f"⚠️  Failed to auto-save task: {e}")
    
    # SELF-LEARNING: Record healing execution for continuous improvement
    if original_command:
        healing_attempts = len(healing_executor.failed_locators) if hasattr(healing_executor, 'failed_locators') else 0
        final_code = healed_code if healed_code else code
        
        self_learning_engine.learn_from_execution(
            command=original_command,
            code=final_code,
            result=result,
            healing_attempts=healing_attempts,
            url=''
        )
    
    socketio.emit('execution_complete', {
        'test_id': test_id,
        'status': status,
        'logs': result.get('logs', []),
        'screenshot_path': screenshot_path,
        'healed_script': healed_code,
        'failed_locators': result.get('failed_locators', [])
    })

def execute_agent_with_healing(test_id, code, browser, mode, auto_save=False, original_command=None):
    """Execute automation on agent with server-coordinated healing."""
    import gevent
    from gevent.event import AsyncResult
    
    # Find the agent's session ID
    agent_sid = None
    for sid in connected_agents:
        agent_sid = sid
        break  # Get the first available agent
    
    healing_executor = HealingExecutor(socketio, api_key=openai_api_key)
    healing_executor.execution_mode = 'agent'  # Mark as agent execution
    healing_executor.agent_sid = agent_sid  # Store agent session ID
    # Use gevent AsyncResult for cross-greenlet communication
    healing_executor.agent_result_async = AsyncResult()
    active_healing_executors[test_id] = healing_executor
    headless = mode == 'headless'
    
    socketio.emit('execution_status', {
        'test_id': test_id,
        'status': 'running',
        'message': f'Executing on agent with healing in {mode} mode...'
    })
    
    # Run async code synchronously using gevent - NO asyncio.run()
    # This keeps us in the same greenlet so socket.io handlers can communicate
    async def _run_healing():
        return await healing_executor.execute_with_healing(code, browser, headless, test_id)
    
    try:
        # Use gevent to wrap the async function
        import nest_asyncio
        nest_asyncio.apply()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(_run_healing())
        finally:
            loop.close()
    finally:
        if test_id in active_healing_executors:
            del active_healing_executors[test_id]
    
    screenshot_path = None
    if result.get('screenshot'):
        screenshot_path = f"screenshots/test_{test_id}.png"
        with open(os.path.join(app.config['UPLOAD_FOLDER'], screenshot_path), 'wb') as f:
            f.write(result['screenshot'])
    
    logs_json = json.dumps(result.get('logs', [])) if result.get('logs') else '[]'
    status = 'success' if result.get('success') else 'failed'
    healed_code = result.get('healed_script')
    
    print(f"\n💾 SAVING TO DATABASE:")
    print(f"  test_id: {test_id}")
    print(f"  status: {status}")
    print(f"  healed_code is None: {healed_code is None}")
    print(f"  healed_code length: {len(healed_code) if healed_code else 0}", flush=True)
    
    conn = sqlite3.connect(app.config['DATABASE_PATH'])
    c = conn.cursor()
    c.execute('UPDATE test_history SET status=?, logs=?, screenshot_path=?, healed_code=? WHERE id=?',
              (status, logs_json, screenshot_path, healed_code, test_id))
    conn.commit()
    conn.close()
    
    # Auto-save successful healed executions as learned tasks
    if auto_save and result.get('success') and original_command and semantic_search:
        try:
            # Use healed code if available, otherwise use original code
            final_code = healed_code if healed_code else code
            task_id = str(uuid.uuid4())
            task_name = original_command[:100]  # Limit name length
            
            task = LearnedTask(
                task_id=task_id,
                task_name=task_name,
                playwright_code=final_code,
                description=f"Auto-saved from agent {'healed' if healed_code else 'execution'} in {mode} mode",
                steps=[],
                tags=[mode, browser, 'auto-saved', 'agent', 'healed' if healed_code else 'standard']
            )
            task.save()
            
            # Index for semantic search
            semantic_search.index_task(task)
            print(f"✅ Auto-saved successful agent {'healed ' if healed_code else ''}execution as learned task: '{task_name}'")
            
            socketio.emit('task_auto_saved', {
                'test_id': test_id,
                'task_id': task_id,
                'task_name': task_name,
                'was_healed': bool(healed_code)
            })
        except Exception as e:
            print(f"⚠️  Failed to auto-save task: {e}")
    
    print(f"  ✅ Database updated successfully", flush=True)
    
    socketio.emit('execution_complete', {
        'test_id': test_id,
        'status': status,
        'logs': result.get('logs', []),
        'screenshot_path': screenshot_path,
        'healed_script': healed_code,
        'failed_locators': result.get('failed_locators', [])
    })

@app.route('/api/heal', methods=['POST'])
def heal_locator():
    data = request.json or {}
    test_id = data.get('test_id')
    failed_locator = data.get('failed_locator')
    healed_locator = data.get('healed_locator')
    
    if not all([test_id, failed_locator, healed_locator]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    try:
        conn = sqlite3.connect(app.config['DATABASE_PATH'])
        c = conn.cursor()
        c.execute('SELECT generated_code, healed_code FROM test_history WHERE id=?', (test_id,))
        row = c.fetchone()
        
        if not row:
            return jsonify({'error': 'Test not found'}), 404
        
        original_code = row[0]
        current_healed = row[1] or original_code
        
        new_healed = current_healed.replace(failed_locator, healed_locator)
        
        c.execute('UPDATE test_history SET healed_code=? WHERE id=?', (new_healed, test_id))
        conn.commit()
        conn.close()
        
        socketio.emit('script_healed', {
            'test_id': test_id,
            'healed_script': new_healed,
            'failed_locator': failed_locator,
            'healed_locator': healed_locator
        })
        
        return jsonify({'success': True, 'healed_script': new_healed})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_DIR_ABS, filename)

@app.route('/api/agent/download')
def download_agent():
    # Get the current server URL dynamically
    replit_domain = os.environ.get('REPLIT_DEV_DOMAIN', 'localhost:5000')
    server_url = f'https://{replit_domain}' if replit_domain != 'localhost:5000' else 'http://localhost:5000'
    
    # Read the local agent file
    with open('visionvault/agents/local_agent.py', 'r', encoding='utf-8') as f:
        agent_code = f.read()
    
    # Replace the default port in get_server_url to prioritize the current server
    # This ensures downloaded agent connects to the right server by default
    agent_code = agent_code.replace(
        'local_ports = [5000, 8000, 3000, 7890]',
        f'# Auto-configured for this server\n    local_ports = [{replit_domain.split(":")[-1] if ":" in replit_domain else "5000"}, 5000, 8000, 3000, 7890]'
    )
    
    # Also add the server URL as a comment for reference
    agent_code = f'# Auto-downloaded from: {server_url}\n# This agent will automatically connect to the server\n\n{agent_code}'
    
    # Create a temporary response with the modified content
    return Response(
        agent_code,
        mimetype='text/x-python',
        headers={'Content-Disposition': 'attachment; filename=local_agent.py'}
    )

# ========== Persistent Learning API Endpoints ==========

@app.route('/api/tasks', methods=['GET'])
def get_all_tasks():
    """Get all learned tasks."""
    try:
        limit = request.args.get('limit', 100, type=int)
        tasks = LearnedTask.get_all(limit=limit)
        return jsonify([task.to_dict() for task in tasks])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tasks/<task_id>', methods=['GET'])
def get_task(task_id):
    """Get a specific learned task."""
    try:
        task = LearnedTask.get_by_id(task_id)
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        return jsonify(task.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tasks/save', methods=['POST'])
def save_learned_task():
    """Save a new learned task or update existing one."""
    try:
        data = request.json or {}
        
        # Extract task data
        task_id = data.get('task_id') or str(uuid.uuid4())
        task_name = data.get('task_name')
        playwright_code = data.get('playwright_code')
        description = data.get('description', '')
        steps = data.get('steps', [])
        tags = data.get('tags', [])
        
        if not task_name or not playwright_code:
            return jsonify({'error': 'task_name and playwright_code are required'}), 400
        
        # Create task object
        task = LearnedTask(
            task_id=task_id,
            task_name=task_name,
            playwright_code=playwright_code,
            description=description,
            steps=steps,
            tags=tags
        )
        
        # Save to database
        task.save()
        
        # Index for semantic search
        if semantic_search:
            try:
                semantic_search.index_task(task)
                print(f"✅ Task '{task_name}' indexed for semantic search")
            except Exception as e:
                print(f"⚠️ Failed to index task for search: {e}")
        
        return jsonify({
            'success': True,
            'task': task.to_dict()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tasks/<task_id>', methods=['DELETE'])
def delete_task(task_id):
    """Delete a learned task."""
    try:
        task = LearnedTask.get_by_id(task_id)
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        # Remove from semantic search index
        if semantic_search:
            semantic_search.delete_task_from_index(task_id)
        
        # Delete from database
        conn = sqlite3.connect(app.config['DATABASE_PATH'])
        c = conn.cursor()
        c.execute('DELETE FROM learned_tasks WHERE task_id=?', (task_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tasks/search', methods=['POST'])
def search_tasks():
    """Search for tasks using natural language."""
    try:
        data = request.json or {}
        query = data.get('query')
        top_k = data.get('top_k', 5)
        
        if not query:
            return jsonify({'error': 'query is required'}), 400
        
        if not semantic_search:
            return jsonify({
                'error': 'OPENAI_API_KEY is not set. Semantic search requires an OpenAI API key to generate embeddings.'
            }), 400
        
        # Search for relevant tasks
        results = semantic_search.search_tasks(query, top_k=top_k)
        
        return jsonify({
            'query': query,
            'results': results
        })
    except Exception as e:
        error_msg = str(e)
        # Check if it's an API key or embedding-related error
        if any(keyword in error_msg.lower() for keyword in ['api', 'key', 'embedding', 'openai', 'authentication', 'unauthorized']):
            return jsonify({
                'error': f'OPENAI_API_KEY error: {error_msg}'
            }), 400
        return jsonify({'error': str(e)}), 500

@app.route('/api/tasks/<task_id>/execute', methods=['POST'])
def execute_learned_task(task_id):
    """Execute a learned task."""
    try:
        data = request.json or {}
        browser = data.get('browser', 'chromium')
        mode = data.get('mode', 'headless')
        execution_location = data.get('execution_location', 'server')
        
        # Get the task
        task = LearnedTask.get_by_id(task_id)
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        # Use the task's code instead of generating new code
        code = task.playwright_code
        
        # Validate the code
        validator = CodeValidator()
        if not validator.validate(code):
            error_msg = "Task code failed security validation: " + "; ".join(validator.get_errors())
            return jsonify({'error': error_msg}), 400
        
        # Create a test history entry for tracking
        conn = sqlite3.connect(app.config['DATABASE_PATH'])
        c = conn.cursor()
        c.execute('INSERT INTO test_history (command, generated_code, browser, mode, execution_location, status) VALUES (?, ?, ?, ?, ?, ?)',
                  (f"Learned Task: {task.task_name}", code, browser, mode, execution_location, 'pending'))
        test_id = c.lastrowid
        conn.commit()
        conn.close()
        
        # Execute the task
        if execution_location == 'server':
            socketio.start_background_task(execute_on_server, test_id, code, browser, mode)
        else:
            agent_sid = None
            for sid in connected_agents:
                agent_sid = sid
                break
            
            if agent_sid:
                socketio.emit('execute_on_agent', {
                    'test_id': test_id,
                    'code': code,
                    'browser': browser,
                    'mode': mode
                }, to=agent_sid)
            else:
                return jsonify({'error': 'No agent connected'}), 503
        
        # Update task execution stats
        start_time = time.time()
        
        # Record execution in background
        def record_execution():
            # Wait a bit for execution to complete
            time.sleep(2)
            
            # Get execution result from test_history
            conn = sqlite3.connect(app.config['DATABASE_PATH'])
            c = conn.cursor()
            c.execute('SELECT status, logs FROM test_history WHERE id=?', (test_id,))
            row = c.fetchone()
            
            if row:
                status = row[0]
                logs = row[1]
                success = status == 'success'
                
                # Update task stats
                task = LearnedTask.get_by_id(task_id)
                if task:
                    if success:
                        task.success_count += 1
                    else:
                        task.failure_count += 1
                    task.last_executed = datetime.now()
                    task.save()
                
                # Record execution
                execution_time = int((time.time() - start_time) * 1000)
                execution = TaskExecution(
                    task_id=task_id,
                    execution_result=status,
                    success=success,
                    error_message=logs if not success else None,
                    execution_time_ms=execution_time
                )
                execution.save()
            
            conn.close()
        
        socketio.start_background_task(record_execution)
        
        return jsonify({
            'test_id': test_id,
            'task_name': task.task_name,
            'message': 'Task execution started'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tasks/recall', methods=['POST'])
def recall_and_execute():
    """
    Recall Mode: Search for a task by natural language and execute it.
    This is the main entry point for the persistent learning system.
    """
    try:
        data = request.json or {}
        query = data.get('query')
        browser = data.get('browser', 'chromium')
        mode = data.get('mode', 'headless')
        execution_location = data.get('execution_location', 'server')
        auto_execute = data.get('auto_execute', False)
        
        if not query:
            return jsonify({'error': 'query is required'}), 400
        
        if not semantic_search:
            return jsonify({
                'error': 'OPENAI_API_KEY is not set. Recall Mode requires an OpenAI API key to search for tasks.'
            }), 400
        
        # Search for the most relevant task
        try:
            results = semantic_search.search_tasks(query, top_k=1)
        except Exception as search_error:
            error_msg = str(search_error)
            if any(keyword in error_msg.lower() for keyword in ['api', 'key', 'embedding', 'openai', 'authentication', 'unauthorized']):
                return jsonify({
                    'error': f'OPENAI_API_KEY error: {error_msg}'
                }), 400
            raise
        
        if not results:
            return jsonify({
                'found': False,
                'message': 'No matching tasks found. Consider creating a new task.'
            })
        
        # Get the best match
        best_match = results[0]
        task_id = best_match['task_id']
        similarity_score = best_match.get('similarity_score', 0)
        
        # If auto_execute is True and similarity is high enough, execute immediately
        if auto_execute and similarity_score > 0.7:
            # Execute the task
            task = LearnedTask.get_by_id(task_id)
            if not task:
                return jsonify({'error': 'Task not found'}), 404
            code = task.playwright_code
            
            # Create test history entry
            conn = sqlite3.connect(app.config['DATABASE_PATH'])
            c = conn.cursor()
            c.execute('INSERT INTO test_history (command, generated_code, browser, mode, execution_location, status) VALUES (?, ?, ?, ?, ?, ?)',
                      (query, code, browser, mode, execution_location, 'pending'))
            test_id = c.lastrowid
            conn.commit()
            conn.close()
            
            # Execute
            if execution_location == 'server':
                socketio.start_background_task(execute_on_server, test_id, code, browser, mode)
            
            return jsonify({
                'found': True,
                'executed': True,
                'test_id': test_id,
                'task': best_match,
                'similarity_score': similarity_score
            })
        else:
            # Return the best match for user confirmation
            return jsonify({
                'found': True,
                'executed': False,
                'task': best_match,
                'similarity_score': similarity_score,
                'message': 'Task found. Please confirm execution or adjust the query.'
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ========== Script Management API Endpoints ==========

@app.route('/api/scripts/download/history/<int:history_id>', methods=['GET'])
def download_script_from_history(history_id):
    """Download a Playwright script from test history."""
    try:
        conn = sqlite3.connect(app.config['DATABASE_PATH'])
        c = conn.cursor()
        c.execute('SELECT command, generated_code, healed_code FROM test_history WHERE id=?', (history_id,))
        row = c.fetchone()
        conn.close()
        
        if not row:
            return jsonify({'error': 'History item not found'}), 404
        
        command, generated_code, healed_code = row
        
        # Use healed code if available, otherwise use generated code
        script_code = healed_code if healed_code else generated_code
        script_type = 'healed' if healed_code else 'generated'
        
        # Create a safe filename from the command
        safe_command = re.sub(r'[^\w\s-]', '', command)[:50]
        safe_command = re.sub(r'[-\s]+', '_', safe_command)
        filename = f"automation_{safe_command}_{script_type}_{history_id}.py"
        
        return Response(
            script_code,
            mimetype='text/x-python',
            headers={'Content-Disposition': f'attachment; filename={filename}'}
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/scripts/download/task/<task_id>', methods=['GET'])
def download_script_from_task(task_id):
    """Download a Playwright script from a learned task."""
    try:
        task = LearnedTask.get_by_id(task_id)
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        # Create a safe filename from the task name
        safe_name = re.sub(r'[^\w\s-]', '', task.task_name)[:50]
        safe_name = re.sub(r'[-\s]+', '_', safe_name)
        filename = f"task_{safe_name}.py"
        
        return Response(
            task.playwright_code,
            mimetype='text/x-python',
            headers={'Content-Disposition': f'attachment; filename={filename}'}
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/scripts/list', methods=['GET'])
def list_all_scripts():
    """List all available scripts from test history and learned tasks."""
    try:
        scripts = []
        
        # Get scripts from test history
        conn = sqlite3.connect(app.config['DATABASE_PATH'])
        c = conn.cursor()
        c.execute('''SELECT id, command, status, created_at, generated_code, healed_code 
                     FROM test_history ORDER BY created_at DESC LIMIT 50''')
        history_rows = c.fetchall()
        
        for row in history_rows:
            history_id, command, status, created_at, generated_code, healed_code = row
            has_healed = bool(healed_code)
            
            scripts.append({
                'id': f'history_{history_id}',
                'source': 'history',
                'history_id': history_id,
                'name': command[:100],
                'description': 'Generated from natural language command',
                'status': status,
                'has_healed': has_healed,
                'script_type': 'healed' if has_healed else 'generated',
                'created_at': created_at,
                'download_url': f'/api/scripts/download/history/{history_id}'
            })
        
        # Get scripts from learned tasks
        c.execute('''SELECT task_id, task_name, description, success_count, failure_count, 
                     created_at FROM learned_tasks ORDER BY created_at DESC LIMIT 50''')
        task_rows = c.fetchall()
        
        for row in task_rows:
            task_id, task_name, description, success_count, failure_count, created_at = row
            success_rate = (success_count / (success_count + failure_count) * 100) if (success_count + failure_count) > 0 else 0
            
            scripts.append({
                'id': f'task_{task_id}',
                'source': 'task',
                'task_id': task_id,
                'name': task_name,
                'description': description or 'Learned automation task',
                'success_count': success_count,
                'failure_count': failure_count,
                'success_rate': round(success_rate, 1),
                'created_at': created_at,
                'download_url': f'/api/scripts/download/task/{task_id}'
            })
        
        conn.close()
        
        return jsonify({'scripts': scripts})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/scripts/compare/<int:history_id>', methods=['GET'])
def compare_scripts(history_id):
    """Compare original and healed scripts to show what changed."""
    try:
        conn = sqlite3.connect(app.config['DATABASE_PATH'])
        c = conn.cursor()
        c.execute('SELECT command, generated_code, healed_code FROM test_history WHERE id=?', (history_id,))
        row = c.fetchone()
        conn.close()
        
        if not row:
            return jsonify({'error': 'History item not found'}), 404
        
        command, generated_code, healed_code = row
        
        if not healed_code:
            return jsonify({
                'has_healed': False,
                'message': 'No healing was performed on this script'
            })
        
        # Simple diff - find differences
        gen_lines = generated_code.split('\n')
        healed_lines = healed_code.split('\n')
        
        changes = []
        for i, (gen_line, healed_line) in enumerate(zip(gen_lines, healed_lines), 1):
            if gen_line != healed_line:
                changes.append({
                    'line': i,
                    'original': gen_line,
                    'healed': healed_line
                })
        
        return jsonify({
            'has_healed': True,
            'command': command,
            'generated_code': generated_code,
            'healed_code': healed_code,
            'changes': changes,
            'total_changes': len(changes)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Teaching Mode Recording - Store recorded actions by session
recording_sessions = {}

@app.route('/api/teaching/start', methods=['POST'])
def start_teaching_recording():
    """Start interactive recording session for Teaching Mode - routes to agent."""
    try:
        data = request.json or {}
        session_id = data.get('session_id') or str(uuid.uuid4())
        # Don't provide default URL - let browser open blank (like Playwright codegen)
        start_url = data.get('start_url', '')
        
        # Check if any agent is connected
        if not connected_agents:
            return jsonify({
                'error': 'No agent connected. Please connect a local agent to use Teaching Mode.',
                'session_id': session_id
            }), 400
        
        # Initialize recording session
        recording_sessions[session_id] = {
            'actions': [],
            'start_time': time.time(),
            'start_url': start_url
        }
        
        # Emit start_recording event to agent
        socketio.emit('start_recording', {
            'session_id': session_id,
            'start_url': start_url
        })
        
        print(f"📤 Sent start_recording to agent for session {session_id}")
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'message': 'Recording request sent to agent. Browser will open on your machine.'
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/teaching/navigate', methods=['POST'])
def teaching_navigate():
    """Navigate to a URL during recording."""
    try:
        data = request.json or {}
        session_id = data.get('session_id')
        url = data.get('url')
        
        if not session_id or session_id not in active_recorders:
            return jsonify({'error': 'No active recording session'}), 400
        
        recorder = active_recorders[session_id]
        loop = active_loops.get(session_id)
        
        if not loop or not recorder.page:
            return jsonify({'error': 'Recording session not ready'}), 400
        
        # Run navigation using the session's event loop
        try:
            asyncio.run_coroutine_threadsafe(recorder.page.goto(url), loop).result(timeout=10)
            recorder.record_goto(url)
            return jsonify({'success': True})
        except Exception as e:
            print(f"Navigation error: {e}")
            return jsonify({'error': str(e)}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/teaching/actions', methods=['GET'])
def get_teaching_actions():
    """Get currently recorded actions."""
    try:
        session_id = request.args.get('session_id')
        
        if not session_id or session_id not in recording_sessions:
            return jsonify({'actions': []})
        
        session = recording_sessions[session_id]
        return jsonify({'actions': session.get('actions', [])})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/teaching/stop', methods=['POST'])
def stop_teaching_recording():
    """Stop recording and return captured actions."""
    try:
        data = request.json or {}
        session_id = data.get('session_id')
        
        if not session_id or session_id not in recording_sessions:
            return jsonify({'error': 'No active recording session'}), 400
        
        # Emit stop_recording event to agent
        socketio.emit('stop_recording', {
            'session_id': session_id
        })
        
        print(f"📤 Sent stop_recording to agent for session {session_id}")
        
        # Return success - actual actions will come via recording_stopped event
        return jsonify({
            'success': True,
            'message': 'Stop request sent to agent'
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/teaching/save_to_library', methods=['POST'])
def save_recording_to_library():
    """Save a recorded session to the task library."""
    try:
        data = request.json or {}
        session_id = data.get('session_id')
        task_name = data.get('task_name')
        description = data.get('description', '')
        tags = data.get('tags', [])
        
        if not session_id or not task_name:
            return jsonify({'error': 'session_id and task_name are required'}), 400
        
        session = recording_sessions.get(session_id)
        if not session:
            return jsonify({'error': 'Recording session not found'}), 404
        
        playwright_code = session.get('playwright_code')
        actions = session.get('actions', [])
        
        if not playwright_code:
            return jsonify({'error': 'No recorded code available'}), 400
        
        task_id = str(uuid.uuid4())
        
        steps = [{'step': i+1, 'description': action.get('description', '')} 
                 for i, action in enumerate(actions)]
        
        task = LearnedTask(
            task_id=task_id,
            task_name=task_name,
            playwright_code=playwright_code,
            description=description,
            steps=steps,
            tags=tags + ['recorded', 'teaching-mode']
        )
        
        task.save()
        
        if semantic_search:
            try:
                semantic_search.index_task(task)
                print(f"✅ Recorded task '{task_name}' indexed for semantic search")
            except Exception as e:
                print(f"⚠️ Failed to index task for search: {e}")
        
        print(f"✅ Recording saved to task library: {task_name} ({task_id})")
        
        return jsonify({
            'success': True,
            'task': task.to_dict(),
            'message': f'Task "{task_name}" saved to library'
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@socketio.on('connect')
def handle_connect():
    print(f'Client connected: {request.sid}')
    emit('connected', {'sid': request.sid})
    # Send current list of connected agents to newly connected web client
    socketio.emit('agents_update', {'agents': list(connected_agents.values())})

@socketio.on('disconnect')
def handle_disconnect():
    print(f'Client disconnected: {request.sid}')
    if request.sid in connected_agents:
        del connected_agents[request.sid]
        print(f'Updated connected_agents after disconnect: {connected_agents}')
        socketio.emit('agents_update', {'agents': list(connected_agents.values())})

@socketio.on('agent_register')
def handle_agent_register(data):
    agent_id = data.get('agent_id')
    connected_agents[request.sid] = {
        'agent_id': agent_id,
        'browsers': data.get('browsers', []),
        'connected_at': datetime.now().isoformat()
    }
    print(f'Agent registered: {agent_id}')
    print(f'Updated connected_agents after register: {connected_agents}')
    emit('agent_registered', {'status': 'success'})
    print(f'Emitting agents_update: {list(connected_agents.values())}')
    socketio.emit('agents_update', {'agents': list(connected_agents.values())})

@socketio.on('agent_result')
def handle_agent_result(data):
    test_id = data.get('test_id')
    success = data.get('success')
    logs = data.get('logs', [])
    screenshot_data = data.get('screenshot')
    
    screenshot_path = None
    if screenshot_data:
        screenshot_path = f"screenshots/test_{test_id}.png"
        screenshot_bytes = base64.b64decode(screenshot_data)
        with open(os.path.join(app.config['UPLOAD_FOLDER'], screenshot_path), 'wb') as f:
            f.write(screenshot_bytes)
    
    logs_json = json.dumps(logs)
    status = 'success' if success else 'failed'
    
    conn = sqlite3.connect(app.config['DATABASE_PATH'])
    c = conn.cursor()
    c.execute('UPDATE test_history SET status=?, logs=?, screenshot_path=? WHERE id=?',
              (status, logs_json, screenshot_path, test_id))
    conn.commit()
    conn.close()
    
    socketio.emit('execution_complete', {
        'test_id': test_id,
        'status': status,
        'logs': logs,
        'screenshot_path': screenshot_path
    })

@socketio.on('agent_log')
def handle_agent_log(data):
    socketio.emit('execution_status', {
        'test_id': data.get('test_id'),
        'status': 'running',
        'message': data.get('message')
    })


@socketio.on('heartbeat')
def handle_heartbeat(data):
    """Handle heartbeat from agent to keep connection alive."""
    # Simply acknowledge - the ping/pong mechanism handles the rest
    # This prevents timeout on idle connections
    pass

@socketio.on('recording_started')
def handle_recording_started(data):
    """Handle recording started event from agent."""
    session_id = data.get('session_id')
    status = data.get('status')
    
    if status == 'success':
        print(f"✅ Recording session {session_id} started on agent")
        socketio.emit('recording_status', {
            'session_id': session_id,
            'status': 'started',
            'message': data.get('message', 'Browser opened on agent machine')
        })
    else:
        error = data.get('error', 'Unknown error')
        print(f"❌ Recording session {session_id} failed to start: {error}")
        socketio.emit('recording_status', {
            'session_id': session_id,
            'status': 'error',
            'error': error
        })


@socketio.on('recording_actions')
def handle_recording_actions(data):
    """Handle periodic action updates from agent."""
    session_id = data.get('session_id')
    actions = data.get('actions', [])
    
    if session_id in recording_sessions:
        recording_sessions[session_id]['actions'].extend(actions)
        print(f"📥 Received {len(actions)} actions for session {session_id}. Total: {len(recording_sessions[session_id]['actions'])}")


@socketio.on('recording_stopped')
def handle_recording_stopped(data):
    """Handle recording stopped event from agent."""
    session_id = data.get('session_id')
    status = data.get('status')
    
    if status == 'success':
        final_actions = data.get('final_actions', [])
        
        if session_id in recording_sessions:
            # Add final actions
            recording_sessions[session_id]['actions'].extend(final_actions)
            all_actions = recording_sessions[session_id]['actions']
            
            print(f"✅ Recording session {session_id} stopped. Total actions: {len(all_actions)}")
            
            # Generate Playwright code from recorded actions
            playwright_code = None
            try:
                if all_actions:
                    playwright_code = generate_playwright_code_from_recording(all_actions)
                    print(f"✅ Generated Playwright code from {len(all_actions)} actions")
            except Exception as e:
                print(f"⚠️ Error generating Playwright code: {e}")
            
            # Emit to web client with both actions and generated code
            socketio.emit('recording_complete', {
                'session_id': session_id,
                'actions': all_actions,
                'playwright_code': playwright_code
            })
    else:
        error = data.get('error', 'Unknown error')
        print(f"❌ Recording session {session_id} stop failed: {error}")
        socketio.emit('recording_status', {
            'session_id': session_id,
            'status': 'error',
            'error': error
        })


@socketio.on('recording_status')
def handle_recording_status(data):
    """Handle recording status updates from agent (including auto-stop on browser close)."""
    session_id = data.get('session_id')
    status = data.get('status')
    
    if status == 'stopped':
        playwright_code = data.get('playwright_code')
        actions = data.get('actions', [])
        auto_stopped = data.get('auto_stopped', False)
        
        print(f"✅ Recording session {session_id} {'auto-' if auto_stopped else ''}stopped")
        print(f"   Playwright code: {'Yes' if playwright_code else 'No'}")
        print(f"   Actions extracted: {len(actions)}")
        
        if session_id in recording_sessions:
            recording_sessions[session_id]['playwright_code'] = playwright_code
            recording_sessions[session_id]['actions'] = actions
        else:
            recording_sessions[session_id] = {
                'playwright_code': playwright_code,
                'actions': actions,
                'start_time': time.time()
            }
        
        socketio.emit('recording_complete', {
            'session_id': session_id,
            'playwright_code': playwright_code,
            'actions': actions,
            'auto_stopped': auto_stopped,
            'message': 'Browser closed. Recording stopped automatically.' if auto_stopped else 'Recording stopped.'
        })
    else:
        socketio.emit('recording_status', data)


@socketio.on('element_selected')
def handle_element_selected(data):
    test_id = data.get('test_id')
    selector = data.get('selector')
    failed_locator = data.get('failed_locator')  # Agent should send this
    
    print(f"\n✅ ELEMENT SELECTED EVENT RECEIVED:")
    print(f"  test_id: {test_id}")
    print(f"  selector: {selector}")
    print(f"  failed_locator: {failed_locator}", flush=True)
    
    # Get the generated code, browser, and mode from database
    conn = sqlite3.connect(app.config['DATABASE_PATH'])
    c = conn.cursor()
    c.execute('SELECT generated_code, browser, mode FROM test_history WHERE id=?', (test_id,))
    row = c.fetchone()
    
    if not row:
        print(f"  ❌ Test {test_id} not found in database", flush=True)
        conn.close()
        socketio.emit('error', {
            'test_id': test_id,
            'message': 'Test not found in database'
        })
        return
    
    generated_code, browser, mode = row
    
    # If failed_locator not provided by agent, try to extract from healing_executor
    if not failed_locator and test_id in active_healing_executors:
        healing_executor = active_healing_executors[test_id]
        if healing_executor.failed_locators:
            failed_locator = healing_executor.failed_locators[-1]['locator']
    
    # Heal the script - replace the entire failed locator method call
    healed_code = generated_code
    
    if failed_locator and selector:
        import re
        
        # If failed_locator is a full method call (e.g., 'page.get_by_placeholder("Search")'),
        # replace the entire method call with the healed selector
        if 'page.' in failed_locator or 'get_by_' in failed_locator or 'locator(' in failed_locator:
            # Try flexible replacement that handles quote variations
            replacement_made = False
            
            # Extract the method and selector from failed_locator
            # E.g., page.locator("input[name=\"q\"]") -> method=page.locator, selector_content=input[name="q"]
            # Handle complex locators with nested parentheses like: page.locator("button:has-text(\"Start Chat\")")
            method_match = re.search(r'(page\.\w+)\((.+)\)$', failed_locator)
            if method_match:
                method_name = method_match.group(1)
                full_args = method_match.group(2)
                
                # Try to extract just the main selector string (first quoted argument)
                selector_match = re.match(r'["\'](.+?)["\']', full_args)
                if selector_match:
                    selector_content = selector_match.group(1)
                    # Escape special regex chars in selector content but not quotes
                    escaped_selector = re.escape(selector_content).replace(r'\"', r'[\\]?"').replace(r"\'", r"[\\]?'")
                    
                    # Build flexible pattern that matches both single and double quotes
                    flexible_pattern = rf'{re.escape(method_name)}\(["\']' + escaped_selector + r'["\'](?:,\s*\w+=.*?)?\)'
                    
                    if re.search(flexible_pattern, healed_code):
                        healed_code = re.sub(flexible_pattern, selector, healed_code, count=1)
                        print(f"  ✅ Replaced full method call (flexible): '{failed_locator}' -> '{selector}'")
                        replacement_made = True
            
            # Fallback to exact match if flexible didn't work
            if not replacement_made:
                escaped_failed = re.escape(failed_locator)
                if re.search(escaped_failed, healed_code):
                    healed_code = re.sub(escaped_failed, selector, healed_code, count=1)
                    print(f"  ✅ Replaced full method call (exact): '{failed_locator}' -> '{selector}'")
                    replacement_made = True
            
            # If still no replacement, try smart contextual replacement
            if not replacement_made:
                print(f"  ⚠️  Could not find failed locator '{failed_locator}' in code")
                print(f"  💡 Trying smart contextual replacement...")
                
                # Extract key text from failed_locator (e.g., "Start Chat" from any locator method)
                text_patterns = [
                    r'name="([^"]+)"',  # name="Start Chat"
                    r'name=\'([^\']+)\'',  # name='Start Chat'
                    r':has-text\(["\']([^"\']+)["\']\)',  # :has-text("Start Chat")
                    r'text="([^"]+)"',  # text="Start Chat"
                    r'text=\'([^\']+)\'',  # text='Start Chat'
                    r'["\']([^"\']*(?:button|link|input)[^"\']*)["\']',  # Any quoted text with element keywords
                ]
                
                key_text = None
                for pattern in text_patterns:
                    match = re.search(pattern, failed_locator, re.IGNORECASE)
                    if match:
                        key_text = match.group(1)
                        break
                
                if key_text:
                    print(f"  🔍 Extracted key text: '{key_text}'")
                    # Find any line containing this text in a locator
                    # Match any page.* method call that contains this text
                    context_pattern = rf'(await\s+)?page\.\w+\([^)]*{re.escape(key_text)}[^)]*\)(?:\.(?:click|fill|type|press|check|select_option)\([^)]*\))?'
                    context_match = re.search(context_pattern, healed_code)
                    
                    if context_match:
                        old_locator_call = context_match.group(0)
                        # Replace the entire locator call with the new selector + action
                        # Extract the action (click, fill, etc.) from the old call
                        action_match = re.search(r'\.(click|fill|type|press|check|select_option)\(([^)]*)\)', old_locator_call)
                        if action_match:
                            action = action_match.group(1)
                            action_args = action_match.group(2)
                            new_call = f"await {selector}.{action}({action_args})"
                            healed_code = healed_code.replace(old_locator_call, new_call, 1)
                            print(f"  ✅ Smart replacement: Found context and replaced entire call")
                            print(f"     Old: {old_locator_call}")
                            print(f"     New: {new_call}")
                            replacement_made = True
                        else:
                            # No action, just replace the locator part
                            healed_code = healed_code.replace(old_locator_call, f"await {selector}", 1)
                            print(f"  ✅ Smart replacement: Replaced locator without action")
                            replacement_made = True
                    else:
                        print(f"  ⚠️  Could not find any locator containing '{key_text}'")
                
                # Last fallback: try simple string replacement
                if not replacement_made:
                    locator_match = re.search(r'["\']([^"\']+)["\']', failed_locator)
                    if locator_match:
                        locator_to_find = locator_match.group(1)
                        if not (selector.startswith('page.') or selector.startswith('get_by_') or 'locator(' in selector):
                            # Simple string replacement
                            escaped_locator = re.escape(locator_to_find)
                            replacement_patterns = [
                                (rf'"{escaped_locator}"', f'"{selector}"'),
                                (rf"'{escaped_locator}'", f"'{selector}'"),
                            ]
                            
                            for pattern, replacement in replacement_patterns:
                                if re.search(pattern, healed_code):
                                    healed_code = re.sub(pattern, replacement, healed_code, count=1)
                                    print(f"  ✅ Replaced locator string: '{locator_to_find}' -> '{selector}'")
                                    replacement_made = True
                                    break
        else:
            # Old logic: failed_locator is just a string selector
            escaped_locator = re.escape(failed_locator)
            replacement_patterns = [
                (rf'"{escaped_locator}"', f'"{selector}"'),
                (rf"'{escaped_locator}'", f"'{selector}'"),
            ]
            
            replacement_made = False
            for pattern, replacement in replacement_patterns:
                if re.search(pattern, healed_code):
                    old_code = healed_code
                    healed_code = re.sub(pattern, replacement, healed_code, count=1)
                    replacement_made = (healed_code != old_code)
                    if replacement_made:
                        print(f"  ✅ Replaced locator: '{failed_locator}' -> '{selector}'")
                        break
            
            if not replacement_made:
                print(f"  ⚠️  Could not find locator '{failed_locator}' in generated code")
                print(f"  💡 User may need to manually update the healed script")
    
    print(f"\n🔧 HEALING SCRIPT IN handle_element_selected:")
    print(f"  Failed locator: '{failed_locator}'")
    print(f"  Healed locator: '{selector}'")
    print(f"  Replacement successful: {healed_code != generated_code}")
    print(f"  Healed code length: {len(healed_code)}", flush=True)
    
    # Save healed code to database
    c.execute('UPDATE test_history SET healed_code=? WHERE id=?', (healed_code, test_id))
    conn.commit()
    conn.close()
    
    print(f"  ✅ Healed code saved to database for test {test_id}", flush=True)
    
    # Update healing executor if it exists
    if test_id in active_healing_executors:
        healing_executor = active_healing_executors[test_id]
        healing_executor.set_user_selector(selector)
        healing_executor.healed_script = healed_code
    
    # Emit confirmation to UI
    socketio.emit('element_selected_confirmed', {
        'test_id': test_id,
        'selector': selector,
        'failed_locator': failed_locator,
        'healed_script': healed_code
    })
    
    # FIX: Trigger re-execution with healed code (final attempt with user-selected locator)
    print(f"\n🚀 TRIGGERING FINAL RETRY with user-selected locator...")
    print(f"  Test ID: {test_id}")
    print(f"  Browser: {browser}")
    print(f"  Mode: {mode}")
    
    # Get agent's session ID from healing executor or connected agents
    agent_sid = None
    if test_id in active_healing_executors:
        agent_sid = active_healing_executors[test_id].agent_sid
        print(f"  Agent SID from executor: {agent_sid}")
    
    if not agent_sid and connected_agents:
        # Fallback to any connected agent
        agent_sid = list(connected_agents.keys())[0]
        print(f"  Using first connected agent: {agent_sid}")
    
    if agent_sid:
        # This is the FINAL manual healing attempt - mark it specially
        # and disable further healing if it fails
        socketio.emit('execute_healing_attempt', {
            'test_id': test_id,
            'code': healed_code,
            'browser': browser or 'chromium',
            'mode': mode or 'headful',
            'attempt': 999,  # Special marker: final manual attempt, no more healing
            'final_manual_attempt': True  # Flag to prevent further healing requests
        }, to=agent_sid)
        print(f"  ✅ FINAL manual healing attempt triggered with healed code to agent {agent_sid}", flush=True)
        
        # Mark that manual healing has been attempted for this test
        # to prevent multiple manual healing widgets
        if test_id in active_healing_executors:
            active_healing_executors[test_id].manual_healing_attempted = True
    else:
        print(f"  ❌ No agent connected - cannot trigger retry", flush=True)
        socketio.emit('error', {
            'test_id': test_id,
            'message': 'No agent connected for retry execution'
        })

@socketio.on('request_ai_healing')
def handle_ai_healing_request(data):
    """
    Handle AI healing request for code generation errors.
    Automatically retries with improved AI prompting based on error type.
    """
    test_id = data.get('test_id')
    error_type = data.get('error_type')
    error_info = data.get('error_info', {})
    attempt = data.get('attempt', 1)
    agent_sid = request.sid  # Get the agent's session ID
    
    print(f"\n🤖 AI HEALING REQUEST:")
    print(f"  Test ID: {test_id}")
    print(f"  Error Type: {error_type}")
    print(f"  Attempt: {attempt}")
    print(f"  Error Detail: {error_info.get('detail', error_info.get('full_error', 'N/A'))[:150]}")
    
    # Get the original code from database
    conn = sqlite3.connect(app.config['DATABASE_PATH'])
    c = conn.cursor()
    c.execute('SELECT generated_code, healed_code, browser, mode FROM test_history WHERE id=?', (test_id,))
    row = c.fetchone()
    
    if not row:
        print(f"  ❌ Test {test_id} not found in database")
        conn.close()
        return
    
    generated_code, existing_healed_code, browser, mode = row
    current_code = existing_healed_code if existing_healed_code else generated_code
    
    # Get or create healing executor
    if test_id not in active_healing_executors:
        openai_key = os.environ.get('OPENAI_API_KEY')
        healing_executor = HealingExecutor(socketio, api_key=openai_key, use_gpt4o=False)
        healing_executor.agent_sid = agent_sid
        active_healing_executors[test_id] = healing_executor
    else:
        healing_executor = active_healing_executors[test_id]
        healing_executor.agent_sid = agent_sid
    
    # Extract error detail
    error_detail = error_info.get('detail', error_info.get('full_error', 'Unknown error'))
    failed_step = error_info.get('step', 0)
    
    # Check max retries (2 AI attempts, then manual widget)
    max_retries = healing_executor.max_retries
    if attempt >= max_retries:
        print(f"  ⚠️ Max AI healing attempts ({max_retries}) reached, triggering manual widget...")
        
        # Trigger manual healing with special attempt number (999) for final manual attempt
        # Agent will show manual widget when it receives attempt >= 999
        socketio.emit('execute_healing_attempt', {
            'test_id': test_id,
            'code': current_code,
            'browser': browser,
            'mode': mode,
            'attempt': 999,
            'final_manual_attempt': True
        }, to=agent_sid)
        print(f"  🎯 Sent manual healing trigger to agent (attempt 999 - final manual attempt)")
        conn.close()
        return
    
    # Use AI to regenerate the code
    print(f"  🔄 Regenerating code with AI (attempt {attempt}/{max_retries})...")
    healed_code = healing_executor.regenerate_code_with_ai(
        current_code,
        error_detail,
        failed_step,
        attempt,
        error_type=error_type
    )
    
    if healed_code and healed_code != current_code:
        # Save healed code to database
        c.execute('UPDATE test_history SET healed_code=? WHERE id=?', (healed_code, test_id))
        conn.commit()
        print(f"  ✅ AI regenerated code saved to database ({len(healed_code)} chars)")
        
        # Send healed code back to agent for retry
        socketio.emit('execute_healing_attempt', {
            'test_id': test_id,
            'code': healed_code,
            'browser': browser,
            'mode': mode,
            'attempt': attempt + 1
        }, to=agent_sid)
        print(f"  🚀 Sent healed code to agent for retry (attempt {attempt + 1}/{max_retries})")
    else:
        print(f"  ⚠️ AI regeneration failed or produced same code")
        # Mark as failed in database
        c.execute('UPDATE test_history SET status=? WHERE id=?', ('failed', test_id))
        conn.commit()
        # Notify agent to close browser
        socketio.emit('healing_complete', {
            'test_id': test_id,
            'success': False,
            'reason': 'regeneration_failed'
        }, to=agent_sid)
    
    conn.close()

@socketio.on('healing_attempt_result')
def handle_healing_attempt_result(data):
    """Handle result from agent healing attempt execution."""
    test_id = data.get('test_id')
    
    if test_id in active_healing_executors:
        healing_executor = active_healing_executors[test_id]
        result = {
            'success': data.get('success'),
            'logs': data.get('logs', []),
            'screenshot': data.get('screenshot')
        }
        # Set via both methods for compatibility
        healing_executor.set_agent_result(result)
        # Also set via gevent AsyncResult for cross-greenlet communication
        if hasattr(healing_executor, 'agent_result_async'):
            healing_executor.agent_result_async.set(result)

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 6890))
    socketio.run(
        app,
        host='127.0.0.1',  # localhost
        port=port,
        debug=True,
        allow_unsafe_werkzeug=True
    )
