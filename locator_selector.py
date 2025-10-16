import logging
from typing import List, Optional, Dict, Any
from models import LocatorCandidate, DOMElement
from dom_analyzer import DOMAnalyzer

logger = logging.getLogger(__name__)

class LocatorSelector:
    def __init__(self, dom_analyzer: DOMAnalyzer, confidence_threshold: float = 0.7):
        self.dom_analyzer = dom_analyzer
        self.confidence_threshold = confidence_threshold
    
    def find_best_locator(self, target_description: str) -> Optional[LocatorCandidate]:
        candidates = self._generate_candidates(target_description)
        
        if not candidates:
            logger.warning(f"No candidates found for: {target_description}")
            return None
        
        candidates.sort(key=lambda c: c.confidence_score, reverse=True)
        
        best_candidate = candidates[0]
        
        logger.info(f"Found {len(candidates)} candidates for '{target_description}'")
        logger.info(f"Best locator: {best_candidate.role or best_candidate.tag_name} "
                   f"(confidence: {best_candidate.confidence_score:.2f})")
        
        if best_candidate.confidence_score < self.confidence_threshold:
            logger.warning(f"Best candidate confidence ({best_candidate.confidence_score:.2f}) "
                         f"below threshold ({self.confidence_threshold})")
        
        return best_candidate
    
    def _generate_candidates(self, target_description: str) -> List[LocatorCandidate]:
        candidates = []
        
        exact_text_matches = self.dom_analyzer.find_elements_by_text(target_description, exact=True)
        for elem in exact_text_matches:
            candidates.append(self._create_candidate(elem, base_score=0.95, reason="exact_text"))
        
        partial_text_matches = self.dom_analyzer.find_elements_by_text(target_description, exact=False)
        for elem in partial_text_matches:
            if elem not in exact_text_matches:
                candidates.append(self._create_candidate(elem, base_score=0.75, reason="partial_text"))
        
        aria_matches = self.dom_analyzer.find_elements_by_aria_label(target_description, exact=False)
        for elem in aria_matches:
            if elem not in exact_text_matches and elem not in partial_text_matches:
                candidates.append(self._create_candidate(elem, base_score=0.85, reason="aria_label"))
        
        placeholder_matches = self.dom_analyzer.find_elements_by_placeholder(target_description, exact=False)
        for elem in placeholder_matches:
            if elem not in exact_text_matches and elem not in partial_text_matches and elem not in aria_matches:
                candidates.append(self._create_candidate(elem, base_score=0.80, reason="placeholder"))
        
        return candidates
    
    def _create_candidate(self, element: DOMElement, base_score: float, reason: str) -> LocatorCandidate:
        confidence_score = base_score
        
        if element.role in ["button", "link", "textbox", "input", "combobox"]:
            confidence_score += 0.05
        
        if element.aria_label:
            confidence_score += 0.03
        
        if element.depth < 5:
            confidence_score += 0.02
        
        if len(element.children) == 0:
            confidence_score += 0.02
        
        confidence_score = min(confidence_score, 1.0)
        
        locator_string = self._build_locator_string(element)
        
        return LocatorCandidate(
            element_id=element.id,
            role=element.role,
            text=element.text,
            aria_label=element.aria_label,
            placeholder=element.placeholder,
            tag_name=element.tag_name,
            confidence_score=confidence_score,
            xpath=element.xpath,
            attributes=element.attributes,
            parent_path=self._get_parent_path(element)
        )
    
    def _build_locator_string(self, element: DOMElement) -> str:
        if element.aria_label:
            return f'[aria-label="{element.aria_label}"]'
        
        if element.text and len(element.text) < 50:
            return f'text="{element.text}"'
        
        if element.placeholder:
            return f'[placeholder="{element.placeholder}"]'
        
        if element.role:
            return f'role={element.role}'
        
        return element.xpath
    
    def _get_parent_path(self, element: DOMElement) -> str:
        path_parts = []
        current_id = element.parent_id
        
        while current_id and current_id in self.dom_analyzer.elements:
            parent = self.dom_analyzer.elements[current_id]
            if parent.role:
                path_parts.append(parent.role)
            elif parent.tag_name:
                path_parts.append(parent.tag_name)
            current_id = parent.parent_id
        
        path_parts.reverse()
        return " > ".join(path_parts) if path_parts else "root"
    
    def get_fallback_locators(self, original_candidate: LocatorCandidate) -> List[LocatorCandidate]:
        fallbacks = []
        
        if original_candidate.element_id in self.dom_analyzer.elements:
            element = self.dom_analyzer.elements[original_candidate.element_id]
            
            if element.text:
                fallbacks.append(self._create_candidate(element, base_score=0.6, reason="text_fallback"))
            
            if element.role:
                role_elements = self.dom_analyzer.find_elements_by_role(element.role)
                for role_elem in role_elements[:3]:
                    if role_elem.id != element.id:
                        fallbacks.append(self._create_candidate(role_elem, base_score=0.5, reason="role_fallback"))
            
            if element.parent_id:
                parent = self.dom_analyzer.elements.get(element.parent_id)
                if parent and parent.children:
                    for child_id in parent.children:
                        if child_id != element.id and child_id in self.dom_analyzer.elements:
                            sibling = self.dom_analyzer.elements[child_id]
                            fallbacks.append(self._create_candidate(sibling, base_score=0.4, reason="sibling_fallback"))
                            break
        
        return fallbacks[:3]
