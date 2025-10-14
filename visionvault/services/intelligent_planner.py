"""
Intelligent Pre-Execution Planner

This module analyzes user commands BEFORE execution to:
1. Predict potential failures and edge cases
2. Generate multiple execution strategies
3. Pre-validate URLs and element availability
4. Optimize execution path for speed and reliability
5. Provide confidence scores and risk assessment
"""

import re
from typing import Dict, List, Optional
from openai import OpenAI


class IntelligentPlanner:
    """AI-powered pre-execution planning and analysis"""
    
    def __init__(self, openai_client: Optional[OpenAI] = None):
        self.client = openai_client
        self.common_patterns = self._load_common_patterns()
    
    def _load_common_patterns(self) -> Dict:
        """Load common automation patterns and success strategies"""
        return {
            'search': {
                'keywords': ['search', 'find', 'look for', 'query'],
                'common_issues': ['search box not visible', 'autocomplete interference', 'slow page load'],
                'best_practices': ['wait for search box', 'use placeholder locator', 'handle autocomplete']
            },
            'login': {
                'keywords': ['login', 'sign in', 'authenticate', 'log in'],
                'common_issues': ['captcha', 'two-factor auth', 'session timeout'],
                'best_practices': ['wait for form', 'check for errors', 'handle redirects']
            },
            'form_fill': {
                'keywords': ['fill', 'enter', 'type', 'input'],
                'common_issues': ['validation errors', 'required fields', 'field not ready'],
                'best_practices': ['wait for field visibility', 'validate after fill', 'handle dropdowns']
            },
            'navigation': {
                'keywords': ['go to', 'navigate', 'open', 'visit'],
                'common_issues': ['slow load', 'redirects', 'cookie banners'],
                'best_practices': ['wait for load state', 'handle popups', 'extended timeout']
            },
            'click': {
                'keywords': ['click', 'press', 'select', 'choose'],
                'common_issues': ['element not clickable', 'covered by overlay', 'not visible'],
                'best_practices': ['scroll into view', 'wait for visible', 'check for overlays']
            }
        }
    
    def analyze_command(self, command: str) -> Dict:
        """
        Analyze command and generate execution plan with risk assessment.
        Returns: {
            'intent': str,
            'complexity': str (low/medium/high),
            'predicted_steps': List[str],
            'potential_issues': List[str],
            'recommended_strategies': List[str],
            'confidence_score': float (0-100),
            'estimated_time': str
        }
        """
        if not self.client:
            return self._basic_analysis(command)
        
        try:
            # Use GPT-4o for deep command understanding
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": """You are an expert automation planner with deep understanding of web applications.

Analyze the user's automation command and provide a detailed execution plan.

Your analysis must include:
1. PRIMARY INTENT: What the user wants to accomplish
2. COMPLEXITY: low/medium/high based on steps and potential issues
3. PREDICTED STEPS: Detailed step-by-step breakdown
4. POTENTIAL ISSUES: Common failures (slow load, dynamic content, overlays, SPAs, auth, etc.)
5. RECOMMENDED STRATEGIES: Best practices to avoid failures
6. CONFIDENCE SCORE: 0-100 based on clarity and feasibility
7. ESTIMATED TIME: Expected execution time (e.g., "10-20 seconds")

Consider:
- Website type (SPA, static, e-commerce, etc.)
- Dynamic content and async loading
- Common UI patterns (modals, dropdowns, autocomplete)
- Potential blockers (captcha, auth, cookies)
- Element stability and visibility
- Network delays and page load times

Return a comprehensive analysis that helps generate flawless code."""},
                    {"role": "user", "content": f"Analyze this automation command and create an execution plan:\n\n{command}"}
                ],
                temperature=0.3
            )
            
            analysis_text = response.choices[0].message.content.strip()
            
            # Parse the AI response into structured format
            return self._parse_ai_analysis(analysis_text, command)
        
        except Exception as e:
            print(f"⚠️  AI planning error: {e}")
            return self._basic_analysis(command)
    
    def _parse_ai_analysis(self, analysis_text: str, command: str) -> Dict:
        """Parse AI analysis into structured format"""
        
        # Extract sections from AI response
        intent = self._extract_section(analysis_text, ['PRIMARY INTENT', 'INTENT', 'PURPOSE'])
        complexity = self._extract_complexity(analysis_text)
        steps = self._extract_list(analysis_text, ['PREDICTED STEPS', 'STEPS', 'EXECUTION STEPS'])
        issues = self._extract_list(analysis_text, ['POTENTIAL ISSUES', 'ISSUES', 'RISKS'])
        strategies = self._extract_list(analysis_text, ['RECOMMENDED STRATEGIES', 'STRATEGIES', 'BEST PRACTICES'])
        confidence = self._extract_confidence(analysis_text)
        time_est = self._extract_section(analysis_text, ['ESTIMATED TIME', 'TIME', 'DURATION'])
        
        return {
            'intent': intent or self._infer_intent(command),
            'complexity': complexity or 'medium',
            'predicted_steps': steps or ['Execute command'],
            'potential_issues': issues or ['Standard web automation risks'],
            'recommended_strategies': strategies or ['Use robust locators', 'Add proper waits'],
            'confidence_score': confidence or 70.0,
            'estimated_time': time_est or '10-30 seconds',
            'full_analysis': analysis_text
        }
    
    def _extract_section(self, text: str, headers: List[str]) -> str:
        """Extract content from a section with given headers"""
        for header in headers:
            pattern = rf"{header}[:\s]+(.+?)(?=\n(?:[A-Z\s]+:|$))"
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()
        return ""
    
    def _extract_list(self, text: str, headers: List[str]) -> List[str]:
        """Extract bulleted or numbered list from text"""
        section = self._extract_section(text, headers)
        if not section:
            return []
        
        # Find list items (bullets, numbers, dashes)
        items = re.findall(r'(?:^|\n)[\s]*(?:[-•*]|\d+\.)\s*(.+)', section)
        if items:
            return [item.strip() for item in items if item.strip()]
        
        # Fallback: split by newlines
        lines = [line.strip() for line in section.split('\n') if line.strip()]
        return lines[:5]  # Limit to 5 items
    
    def _extract_complexity(self, text: str) -> str:
        """Extract complexity level"""
        text_lower = text.lower()
        if 'complexity: low' in text_lower or 'low complexity' in text_lower:
            return 'low'
        elif 'complexity: high' in text_lower or 'high complexity' in text_lower:
            return 'high'
        elif 'complexity: medium' in text_lower or 'medium complexity' in text_lower:
            return 'medium'
        return 'medium'
    
    def _extract_confidence(self, text: str) -> float:
        """Extract confidence score"""
        # Look for patterns like "85%", "confidence: 90", etc.
        patterns = [
            r'confidence[:\s]+(\d+)',
            r'(\d+)%?\s*confidence',
            r'score[:\s]+(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return float(match.group(1))
        
        return 75.0  # Default confidence
    
    def _basic_analysis(self, command: str) -> Dict:
        """Fallback analysis without AI"""
        intent = self._infer_intent(command)
        pattern = self._match_pattern(command)
        
        return {
            'intent': intent,
            'complexity': 'medium',
            'predicted_steps': [f'Execute: {command}'],
            'potential_issues': pattern.get('common_issues', ['Standard risks']) if pattern else ['Standard risks'],
            'recommended_strategies': pattern.get('best_practices', ['Use robust locators']) if pattern else ['Use robust locators'],
            'confidence_score': 70.0,
            'estimated_time': '10-30 seconds',
            'full_analysis': 'Basic analysis (AI not available)'
        }
    
    def _infer_intent(self, command: str) -> str:
        """Infer user intent from command"""
        command_lower = command.lower()
        
        if any(kw in command_lower for kw in ['search', 'find', 'look for']):
            return 'Search for information'
        elif any(kw in command_lower for kw in ['login', 'sign in', 'log in']):
            return 'Authenticate user'
        elif any(kw in command_lower for kw in ['buy', 'purchase', 'order']):
            return 'Complete purchase'
        elif any(kw in command_lower for kw in ['fill', 'enter', 'submit']):
            return 'Fill and submit form'
        elif any(kw in command_lower for kw in ['click', 'press', 'select']):
            return 'Interact with element'
        elif any(kw in command_lower for kw in ['go to', 'navigate', 'open', 'visit']):
            return 'Navigate to page'
        else:
            return 'Execute automation task'
    
    def _match_pattern(self, command: str) -> Optional[Dict]:
        """Match command to known patterns"""
        command_lower = command.lower()
        
        for pattern_name, pattern in self.common_patterns.items():
            if any(kw in command_lower for kw in pattern['keywords']):
                return pattern
        
        return None
    
    def generate_optimized_prompt(self, command: str, analysis: Dict) -> str:
        """
        Generate enhanced prompt for code generation based on analysis.
        Includes predicted issues and recommended strategies.
        """
        strategies_text = '\n'.join([f"- {s}" for s in analysis['recommended_strategies']])
        issues_text = '\n'.join([f"- {s}" for s in analysis['potential_issues']])
        
        enhanced_prompt = f"""Generate Playwright code for: {command}

EXECUTION PLAN ANALYSIS:
Intent: {analysis['intent']}
Complexity: {analysis['complexity']}
Confidence: {analysis['confidence_score']:.0f}%

PREDICTED POTENTIAL ISSUES:
{issues_text}

REQUIRED STRATEGIES (MANDATORY):
{strategies_text}

CRITICAL REQUIREMENTS:
1. Implement ALL recommended strategies above
2. Add robust error handling for predicted issues
3. Use intelligent waits (wait_for_load_state, wait_for_selector with visible/attached states)
4. Include retry logic for dynamic content
5. Handle common blockers (cookie banners, overlays, modals)
6. Add detailed logging for each step
7. Use the most reliable locators (testId > role > placeholder > label > text)
8. Set appropriate timeouts (10000ms for critical operations)

Generate production-ready code that anticipates and handles these issues proactively."""
        
        return enhanced_prompt
