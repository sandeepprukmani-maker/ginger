import logging
from typing import Dict, List, Optional, Any
from models import DOMElement
import json

logger = logging.getLogger(__name__)

class DOMAnalyzer:
    def __init__(self):
        self.elements: Dict[str, DOMElement] = {}
        self.element_counter = 0
        
    def analyze_accessibility_tree(self, snapshot_data: Dict[str, Any]) -> int:
        self.elements.clear()
        self.element_counter = 0
        
        if not snapshot_data or "result" not in snapshot_data:
            logger.warning("Invalid snapshot data received")
            return 0
        
        tree_data = snapshot_data.get("result", {})
        
        if isinstance(tree_data, dict):
            self._parse_node(tree_data, depth=0, parent_id=None, xpath="/")
        elif isinstance(tree_data, list):
            for idx, node in enumerate(tree_data):
                self._parse_node(node, depth=0, parent_id=None, xpath=f"/[{idx}]")
        
        logger.info(f"DOM Analysis complete: {len(self.elements)} elements indexed")
        return len(self.elements)
    
    def _parse_node(self, node: Dict[str, Any], depth: int, parent_id: Optional[str], xpath: str):
        if not isinstance(node, dict):
            return
        
        element_id = f"elem_{self.element_counter}"
        self.element_counter += 1
        
        tag_name = node.get("tagName", node.get("role", "unknown"))
        role = node.get("role")
        text = node.get("name") or node.get("text") or node.get("value", "")
        aria_label = node.get("aria-label", node.get("ariaLabel"))
        placeholder = node.get("placeholder")
        
        attributes = {}
        for key, value in node.items():
            if key not in ["children", "childIds", "tagName", "role", "name", "text"]:
                attributes[key] = value
        
        current_xpath = f"{xpath}/{tag_name}"
        if text and len(text) < 30:
            current_xpath += f"[contains(text(),'{text[:20]}')]"
        
        element = DOMElement(
            id=element_id,
            tag_name=tag_name,
            role=role,
            text=text if text else None,
            aria_label=aria_label,
            placeholder=placeholder,
            attributes=attributes,
            xpath=current_xpath,
            parent_id=parent_id,
            children=[],
            depth=depth
        )
        
        self.elements[element_id] = element
        
        if parent_id and parent_id in self.elements:
            self.elements[parent_id].children.append(element_id)
        
        children = node.get("children", [])
        if not children and "childIds" in node:
            children = node.get("childIds", [])
        
        for idx, child in enumerate(children):
            self._parse_node(child, depth + 1, element_id, f"{current_xpath}[{idx}]")
    
    def find_elements_by_text(self, text: str, exact: bool = True) -> List[DOMElement]:
        results = []
        search_text = text.lower()
        
        for element in self.elements.values():
            element_text = (element.text or "").lower()
            
            if exact and element_text == search_text:
                results.append(element)
            elif not exact and search_text in element_text:
                results.append(element)
        
        return results
    
    def find_elements_by_role(self, role: str) -> List[DOMElement]:
        return [elem for elem in self.elements.values() if elem.role == role]
    
    def find_elements_by_aria_label(self, label: str, exact: bool = False) -> List[DOMElement]:
        results = []
        search_label = label.lower()
        
        for element in self.elements.values():
            if element.aria_label:
                element_label = element.aria_label.lower()
                if exact and element_label == search_label:
                    results.append(element)
                elif not exact and search_label in element_label:
                    results.append(element)
        
        return results
    
    def find_elements_by_placeholder(self, placeholder: str, exact: bool = False) -> List[DOMElement]:
        results = []
        search_placeholder = placeholder.lower()
        
        for element in self.elements.values():
            if element.placeholder:
                element_placeholder = element.placeholder.lower()
                if exact and element_placeholder == search_placeholder:
                    results.append(element)
                elif not exact and search_placeholder in element_placeholder:
                    results.append(element)
        
        return results
    
    def get_element_context(self, element_id: str) -> Dict[str, Any]:
        if element_id not in self.elements:
            return {}
        
        element = self.elements[element_id]
        
        parent_chain = []
        current_id = element.parent_id
        while current_id and current_id in self.elements:
            parent = self.elements[current_id]
            parent_chain.append({
                "tag": parent.tag_name,
                "role": parent.role,
                "text": parent.text
            })
            current_id = parent.parent_id
        
        children = [
            {
                "tag": self.elements[child_id].tag_name,
                "role": self.elements[child_id].role,
                "text": self.elements[child_id].text
            }
            for child_id in element.children if child_id in self.elements
        ]
        
        return {
            "element": element.model_dump(),
            "parents": parent_chain,
            "children": children
        }
    
    def export_tree(self) -> Dict[str, Any]:
        return {
            "total_elements": len(self.elements),
            "elements": {eid: elem.model_dump() for eid, elem in self.elements.items()}
        }
