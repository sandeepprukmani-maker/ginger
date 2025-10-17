import os
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from .logger import get_logger
from .advanced_tools import PageContext

logger = get_logger()


@dataclass
class ElementLocation:
    """Location and description of an element found via vision."""
    description: str
    suggested_selector: str
    confidence: float
    position: str  # e.g., "top-left", "center", "bottom-right"
    element_type: str  # e.g., "button", "link", "input"


class VisionPageAnalyzer:
    """
    Uses GPT-4 Vision to understand page structure and locate elements.
    Provides intelligent element detection when traditional selectors fail.
    """
    
    def __init__(self):
        self.client = None
        api_key = os.getenv("OPENAI_API_KEY")
        
        if not OPENAI_AVAILABLE:
            logger.warning("OpenAI package not available for vision analysis")
        elif not api_key:
            logger.warning("OPENAI_API_KEY not set for vision analysis")
        else:
            self.client = AsyncOpenAI(api_key=api_key)
    
    async def analyze_page_structure(self, context: PageContext) -> Dict[str, Any]:
        """
        Analyze page structure using vision to understand layout and elements.
        """
        if not self.client or not context.screenshot_base64:
            logger.warning("Vision analysis not available")
            return {}
        
        logger.info("Analyzing page structure with vision...")
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",  # Using mini for cost efficiency, upgrade to gpt-4o for better vision
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert at analyzing web page screenshots.
Identify all interactive elements, their types, positions, and suggest CSS selectors.
Describe the page layout and main sections."""
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"""Analyze this web page screenshot. 

Page URL: {context.url}
Page Title: {context.title}
Visible Elements Count: {len(context.visible_elements)}

Provide:
1. Page layout description
2. Main sections identified
3. All interactive elements (buttons, links, forms, inputs)
4. Suggested selectors for key elements
5. Any notable UI patterns or frameworks detected

Format as JSON."""
                            }
                        ]
                    }
                ],
                max_tokens=1500,
                temperature=0.3
            )
            
            content = response.choices[0].message.content
            logger.success("Vision analysis completed")
            
            return {"analysis": content, "model_used": "gpt-4o-mini"}
            
        except Exception as e:
            logger.error(f"Vision analysis error: {e}")
            return {}
    
    async def find_element_by_description(self, context: PageContext, 
                                         description: str) -> Optional[ElementLocation]:
        """
        Find an element on the page using visual analysis and natural language description.
        """
        if not self.client or not context.screenshot_base64:
            return None
        
        logger.info(f"Finding element by vision: {description}")
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert at locating elements in web page screenshots.
Given a description, identify the element's position and suggest the best CSS selector.
Respond in JSON format with: description, selector, confidence, position, type."""
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"""Find this element: "{description}"

Page context:
- URL: {context.url}
- Title: {context.title}
- Visible elements: {len(context.visible_elements)}

Provide JSON with:
- description: what you found
- suggested_selector: CSS selector to locate it
- confidence: 0.0 to 1.0
- position: where on page (top-left, center, etc)
- element_type: button, link, input, etc."""
                            }
                        ]
                    }
                ],
                max_tokens=300,
                temperature=0.2
            )
            
            import json
            content = response.choices[0].message.content
            
            if content.startswith("```json"):
                content = content[7:-3]
            elif content.startswith("```"):
                content = content[3:-3]
            content = content.strip()
            
            data = json.loads(content)
            
            location = ElementLocation(
                description=data.get("description", description),
                suggested_selector=data.get("suggested_selector", ""),
                confidence=float(data.get("confidence", 0.5)),
                position=data.get("position", "unknown"),
                element_type=data.get("element_type", "unknown")
            )
            
            logger.success(f"Vision found element: {location.suggested_selector} (confidence: {location.confidence})")
            return location
            
        except Exception as e:
            logger.error(f"Vision element finding error: {e}")
            return None
    
    async def suggest_next_action(self, context: PageContext, goal: str) -> Optional[str]:
        """
        Use vision to suggest the next best action to achieve a goal.
        """
        if not self.client or not context.screenshot_base64:
            return None
        
        logger.info(f"Getting vision suggestion for goal: {goal}")
        
        try:
            dom_context = ""
            if context.visible_elements:
                dom_context = "Visible elements:\n" + "\n".join(context.visible_elements[:20])
            
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert at browser automation.
Analyze the page and suggest the next action to achieve the user's goal.
Be specific about which element to interact with and what action to take."""
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"""Goal: {goal}

Current page:
- URL: {context.url}
- Title: {context.title}

{dom_context}

What should be the next action? Suggest one specific action with element selector."""
                            }
                        ]
                    }
                ],
                max_tokens=200,
                temperature=0.3
            )
            
            suggestion = response.choices[0].message.content
            logger.info(f"Vision suggestion: {suggestion}")
            return suggestion
            
        except Exception as e:
            logger.error(f"Vision suggestion error: {e}")
            return None
    
    async def diagnose_error(self, context: PageContext, error_message: str, 
                            failed_selector: str) -> Optional[str]:
        """
        Use vision to diagnose why an action failed and suggest corrections.
        """
        if not self.client or not context.screenshot_base64:
            return None
        
        logger.info("Using vision to diagnose error...")
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert at debugging browser automation failures.
Analyze the screenshot and error to determine what went wrong and suggest a fix."""
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"""An automation action failed:

Error: {error_message}
Failed selector: {failed_selector}
Page URL: {context.url}
Page Title: {context.title}

Why did it fail? What selector should be used instead?
Provide a corrected selector and explanation."""
                            }
                        ]
                    }
                ],
                max_tokens=300,
                temperature=0.3
            )
            
            diagnosis = response.choices[0].message.content
            logger.info(f"Vision diagnosis: {diagnosis}")
            return diagnosis
            
        except Exception as e:
            logger.error(f"Vision diagnosis error: {e}")
            return None
