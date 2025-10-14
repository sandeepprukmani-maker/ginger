"""
Self-Learning Engine

This module enables the system to:
1. Learn from successful executions and failures
2. Build a knowledge base of working patterns
3. Adapt strategies based on past performance
4. Predict success probability for new commands
5. Continuously improve over time
"""

import json
import os
from typing import Dict, List, Optional
from datetime import datetime
import hashlib


class SelfLearningEngine:
    """AI system that learns from experience and improves over time"""
    
    def __init__(self, knowledge_file='data/learned_knowledge.json'):
        self.knowledge_file = knowledge_file
        self.knowledge_base = self._load_knowledge()
        self.session_learnings = []
    
    def _load_knowledge(self) -> Dict:
        """Load accumulated knowledge from disk"""
        try:
            if os.path.exists(self.knowledge_file):
                with open(self.knowledge_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"⚠️  Could not load knowledge base: {e}")
        
        return {
            'successful_patterns': {},  # Patterns that consistently work
            'failure_patterns': {},      # Patterns that consistently fail
            'locator_success_rates': {}, # Success rate per locator type
            'website_patterns': {},      # Learned patterns per website
            'command_patterns': {},      # Common command structures
            'total_executions': 0,
            'total_successes': 0,
            'total_failures': 0,
            'success_rate': 0.0
        }
    
    def _save_knowledge(self):
        """Persist knowledge to disk"""
        try:
            os.makedirs(os.path.dirname(self.knowledge_file), exist_ok=True)
            
            # Update success rate
            if self.knowledge_base['total_executions'] > 0:
                self.knowledge_base['success_rate'] = (
                    self.knowledge_base['total_successes'] / 
                    self.knowledge_base['total_executions'] * 100
                )
            
            with open(self.knowledge_file, 'w') as f:
                json.dump(self.knowledge_base, f, indent=2)
        except Exception as e:
            print(f"⚠️  Could not save knowledge base: {e}")
    
    def learn_from_execution(
        self,
        command: str,
        code: str,
        result: Dict,
        healing_attempts: int = 0,
        url: str = ''
    ):
        """Learn from a completed execution (successful or failed)"""
        
        success = result.get('success', False)
        
        # Update global stats
        self.knowledge_base['total_executions'] += 1
        if success:
            self.knowledge_base['total_successes'] += 1
        else:
            self.knowledge_base['total_failures'] += 1
        
        # Extract patterns
        command_pattern = self._extract_command_pattern(command)
        locators_used = self._extract_locators(code)
        website = self._extract_website(url or code)
        
        # Learn command patterns
        if command_pattern not in self.knowledge_base['command_patterns']:
            self.knowledge_base['command_patterns'][command_pattern] = {
                'total': 0,
                'successes': 0,
                'avg_healing_attempts': 0.0,
                'best_locators': []
            }
        
        pattern_data = self.knowledge_base['command_patterns'][command_pattern]
        pattern_data['total'] += 1
        if success:
            pattern_data['successes'] += 1
        
        # Update average healing attempts
        pattern_data['avg_healing_attempts'] = (
            (pattern_data['avg_healing_attempts'] * (pattern_data['total'] - 1) + healing_attempts) /
            pattern_data['total']
        )
        
        # Learn locator success rates
        for locator_type in locators_used:
            if locator_type not in self.knowledge_base['locator_success_rates']:
                self.knowledge_base['locator_success_rates'][locator_type] = {
                    'total': 0,
                    'successes': 0,
                    'success_rate': 0.0
                }
            
            loc_data = self.knowledge_base['locator_success_rates'][locator_type]
            loc_data['total'] += 1
            if success:
                loc_data['successes'] += 1
            loc_data['success_rate'] = (loc_data['successes'] / loc_data['total'] * 100)
            
            # Track best locators for this command pattern
            if success and locator_type not in pattern_data['best_locators']:
                pattern_data['best_locators'].append(locator_type)
        
        # Learn website-specific patterns
        if website:
            if website not in self.knowledge_base['website_patterns']:
                self.knowledge_base['website_patterns'][website] = {
                    'total_visits': 0,
                    'successful_locators': [],
                    'common_issues': [],
                    'best_practices': []
                }
            
            site_data = self.knowledge_base['website_patterns'][website]
            site_data['total_visits'] += 1
            
            if success:
                for loc in locators_used:
                    if loc not in site_data['successful_locators']:
                        site_data['successful_locators'].append(loc)
        
        # Record session learning
        self.session_learnings.append({
            'command': command,
            'success': success,
            'healing_attempts': healing_attempts,
            'timestamp': datetime.now().isoformat()
        })
        
        # Save knowledge
        self._save_knowledge()
        
        print(f"📚 Learning recorded: {command_pattern} ({'✅ Success' if success else '❌ Failed'})")
    
    def _extract_command_pattern(self, command: str) -> str:
        """Extract high-level pattern from command"""
        command_lower = command.lower()
        
        patterns = {
            'search': ['search', 'find', 'look for', 'query'],
            'login': ['login', 'sign in', 'log in', 'authenticate'],
            'form_fill': ['fill', 'enter', 'type', 'input'],
            'navigation': ['go to', 'navigate', 'open', 'visit'],
            'click': ['click', 'press', 'select', 'choose'],
            'purchase': ['buy', 'purchase', 'order', 'checkout'],
            'extract': ['get', 'extract', 'scrape', 'collect']
        }
        
        for pattern, keywords in patterns.items():
            if any(kw in command_lower for kw in keywords):
                return pattern
        
        return 'general'
    
    def _extract_locators(self, code: str) -> List[str]:
        """Extract locator types used in code"""
        locators = []
        
        locator_patterns = {
            'get_by_test_id': 'testid',
            'get_by_role': 'role',
            'get_by_text': 'text',
            'get_by_placeholder': 'placeholder',
            'get_by_label': 'label',
            'get_by_alt_text': 'alt',
            'get_by_title': 'title',
            'page.locator': 'css_selector'
        }
        
        for pattern, loc_type in locator_patterns.items():
            if pattern in code:
                locators.append(loc_type)
        
        return list(set(locators))  # Unique locators
    
    def _extract_website(self, url_or_code: str) -> str:
        """Extract website domain"""
        import re
        
        # Try to find URL in string
        url_pattern = r'https?://(?:www\.)?([^/\s]+)'
        match = re.search(url_pattern, url_or_code)
        
        if match:
            domain = match.group(1)
            # Remove common subdomains
            domain = domain.replace('www.', '')
            return domain
        
        return ''
    
    def get_recommendations(self, command: str, url: str = '') -> Dict:
        """Get learned recommendations for a command"""
        
        pattern = self._extract_command_pattern(command)
        website = self._extract_website(url)
        
        recommendations = {
            'predicted_success_rate': self.knowledge_base.get('success_rate', 70.0),
            'recommended_locators': [],
            'potential_issues': [],
            'best_practices': [],
            'confidence': 70.0
        }
        
        # Get command pattern recommendations
        if pattern in self.knowledge_base['command_patterns']:
            pattern_data = self.knowledge_base['command_patterns'][pattern]
            
            if pattern_data['total'] > 0:
                pattern_success_rate = (pattern_data['successes'] / pattern_data['total'] * 100)
                recommendations['predicted_success_rate'] = pattern_success_rate
                recommendations['recommended_locators'] = pattern_data['best_locators']
                recommendations['confidence'] = min(90, 50 + pattern_data['total'] * 5)
        
        # Get website-specific recommendations
        if website and website in self.knowledge_base['website_patterns']:
            site_data = self.knowledge_base['website_patterns'][website]
            recommendations['recommended_locators'].extend(site_data['successful_locators'])
            recommendations['potential_issues'] = site_data.get('common_issues', [])
            recommendations['best_practices'] = site_data.get('best_practices', [])
        
        # Get best performing locators overall
        best_locators = sorted(
            self.knowledge_base['locator_success_rates'].items(),
            key=lambda x: x[1]['success_rate'],
            reverse=True
        )[:3]
        
        for loc_type, data in best_locators:
            if loc_type not in recommendations['recommended_locators']:
                recommendations['recommended_locators'].append(loc_type)
        
        return recommendations
    
    def get_learning_stats(self) -> Dict:
        """Get learning statistics"""
        return {
            'total_executions': self.knowledge_base['total_executions'],
            'overall_success_rate': self.knowledge_base['success_rate'],
            'patterns_learned': len(self.knowledge_base['command_patterns']),
            'websites_learned': len(self.knowledge_base['website_patterns']),
            'locator_types_tracked': len(self.knowledge_base['locator_success_rates']),
            'best_locators': self._get_best_locators(3),
            'session_learnings': len(self.session_learnings)
        }
    
    def _get_best_locators(self, top_n: int = 3) -> List[Dict]:
        """Get top N best performing locators"""
        locators = [
            {
                'type': loc_type,
                'success_rate': data['success_rate'],
                'total_uses': data['total']
            }
            for loc_type, data in self.knowledge_base['locator_success_rates'].items()
            if data['total'] >= 3  # Minimum 3 uses for statistical significance
        ]
        
        # Sort by success rate, then by total uses
        locators.sort(key=lambda x: (x['success_rate'], x['total_uses']), reverse=True)
        
        return locators[:top_n]
