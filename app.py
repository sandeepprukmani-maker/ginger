import asyncio
import os
import streamlit as st

from browser_use import Agent

st.set_page_config(
    page_title="Local Browser Automation",
    page_icon="🔧",
    layout="wide"
)

st.title("🔧 Local Browser Automation")
st.markdown("""
Welcome to Local Browser Automation! This AI agent can automate browser tasks locally on your machine.

**How to get started:**
1. Choose your LLM provider (OpenAI, Anthropic, Google, Ollama, etc.)
2. Add your API key using the sidebar (required for AI models only)
3. Enter a task and click "Run Task"

**Example tasks:**
- "Search Google for the latest news about AI"
- "Find the number of GitHub stars for popular AI repos"
- "Navigate to a website and extract information"
""")

with st.sidebar:
    st.header("⚙️ Configuration")
    
    llm_provider = st.selectbox(
        "LLM Provider",
        ["OpenAI", "Anthropic (Claude)", "Google (Gemini)", "Ollama (Local)"],
        help="Choose your AI model provider"
    )
    
    if llm_provider == "OpenAI":
        api_key = st.text_input(
            "OpenAI API Key",
            type="password",
            help="Your OpenAI API key",
            value=os.getenv("OPENAI_API_KEY", "")
        )
        model = st.selectbox("Model", ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"])
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
    elif llm_provider == "Anthropic (Claude)":
        api_key = st.text_input(
            "Anthropic API Key",
            type="password",
            help="Your Anthropic API key",
            value=os.getenv("ANTHROPIC_API_KEY", "")
        )
        model = st.selectbox("Model", ["claude-3-5-sonnet-20241022", "claude-3-opus-20240229"])
        if api_key:
            os.environ["ANTHROPIC_API_KEY"] = api_key
    elif llm_provider == "Google (Gemini)":
        api_key = st.text_input(
            "Google API Key",
            type="password",
            help="Your Google API key",
            value=os.getenv("GOOGLE_API_KEY", "")
        )
        model = st.selectbox("Model", ["gemini-2.0-flash-exp", "gemini-pro"])
        if api_key:
            os.environ["GOOGLE_API_KEY"] = api_key
    else:
        api_key = None
        model = st.text_input("Model", value="llama3.2", help="Ollama model name")
    
    if api_key:
        st.success("✓ API Key configured")
    elif llm_provider != "Ollama (Local)":
        st.warning("⚠️ Please add your API key")
    
    st.divider()
    
    headless = st.checkbox(
        "Headless Mode",
        value=False,
        help="Run browser in background (no visible window)"
    )
    
    st.divider()
    
    st.markdown("""
    **Privacy Notice:**
    - All processing runs locally on your machine
    - No telemetry or analytics
    - Browser data stays on your computer
    - Only API calls to your chosen LLM provider
    """)

task = st.text_area(
    "Task Description",
    placeholder="E.g., Find information about the latest AI news",
    height=100,
    help="Describe what you want the browser agent to do"
)

col1, col2 = st.columns([1, 5])
with col1:
    run_enabled = (llm_provider == "Ollama (Local)") or (api_key is not None and api_key != "")
    run_button = st.button("🚀 Run Task", type="primary", disabled=not run_enabled)

if run_button and task:
    if llm_provider != "Ollama (Local)" and (not api_key or api_key == ""):
        st.error("Please provide a valid API key in the sidebar.")
    else:
        with st.spinner("Running automation task locally..."):
            try:
                async def run_task():
                    from browser_use import Browser
                    
                    browser = Browser(
                        headless=headless,
                    )
                    
                    if llm_provider == "OpenAI":
                        from browser_use import ChatOpenAI
                        llm = ChatOpenAI(model=model)
                    elif llm_provider == "Anthropic (Claude)":
                        from browser_use.llm.anthropic.chat import ChatAnthropic
                        llm = ChatAnthropic(model=model)
                    elif llm_provider == "Google (Gemini)":
                        from browser_use.llm.google.chat import ChatGoogle
                        llm = ChatGoogle(model=model)
                    else:
                        from browser_use.llm.ollama.chat import ChatOllama
                        llm = ChatOllama(model=model)
                    
                    agent = Agent(
                        task=task,
                        llm=llm,
                        browser=browser,
                    )
                    
                    result = await agent.run()
                    return result
                
                result = asyncio.run(run_task())
                
                st.success("✅ Task completed!")
                
                st.subheader("Results")
                
                if result and hasattr(result, 'final_result'):
                    st.write(result.final_result())
                elif result:
                    st.write(str(result))
                else:
                    st.info("Task completed but no result was returned.")
                    
            except Exception as e:
                st.error(f"Error running task: {str(e)}")
                st.exception(e)

st.divider()

st.markdown("""
### 📚 Local Setup
- **Browser**: Chromium (auto-installed via Playwright)
- **Privacy**: No external data collection
- **Open Source**: Built on browser automation libraries
""")
