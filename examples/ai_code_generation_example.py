import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.automation import AITaskGenerator
from src.automation.config import AutomationConfig
from src.automation.logger import get_logger
from dotenv import load_dotenv

load_dotenv()

logger = get_logger()


async def main():
    config = AutomationConfig(
        openai_model="gpt-4o-mini",
        mcp_timeout=300
    )
    
    generator = AITaskGenerator(config)
    
    logger.info("Generating Playwright code using AI")
    
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python ai_code_generation_example.py '<task description>'")
        print("Example: python ai_code_generation_example.py 'Navigate to a news site and extract article titles'")
        sys.exit(1)
    
    task_description = sys.argv[1]
    
    code = await generator.generate_playwright_code(task_description)
    
    if code:
        logger.success("\n=== Generated Code ===")
        print(code)
        
        output_file = "generated_code.py"
        with open(output_file, 'w') as f:
            f.write(code)
        logger.success(f"\nCode saved to {output_file}")
    else:
        logger.error("Failed to generate code. Make sure OPENAI_API_KEY is set.")


if __name__ == "__main__":
    asyncio.run(main())
