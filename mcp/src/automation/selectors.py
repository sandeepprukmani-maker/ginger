from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum
from playwright.async_api import Page, Locator
from .config import SelectorStrategy
from .logger import get_logger

logger = get_logger()


@dataclass
class SelectorOptions:
    strategy: SelectorStrategy = SelectorStrategy.AUTO
    timeout: int = 10000
    state: str = "visible"
    strict: bool = False


class SmartSelector:
    
    @staticmethod
    async def find_element(
        page: Page,
        selector: str,
        options: Optional[SelectorOptions] = None
    ) -> Optional[Locator]:
        if options is None:
            options = SelectorOptions()
        
        if options.strategy == SelectorStrategy.AUTO:
            return await SmartSelector._auto_select(page, selector, options)
        elif options.strategy == SelectorStrategy.CSS:
            return await SmartSelector._css_select(page, selector, options)
        elif options.strategy == SelectorStrategy.XPATH:
            return await SmartSelector._xpath_select(page, selector, options)
        elif options.strategy == SelectorStrategy.TEXT:
            return await SmartSelector._text_select(page, selector, options)
        elif options.strategy == SelectorStrategy.ARIA:
            return await SmartSelector._aria_select(page, selector, options)
    
    @staticmethod
    async def _auto_select(page: Page, selector: str, options: SelectorOptions) -> Optional[Locator]:
        strategies = [
            (SelectorStrategy.CSS, SmartSelector._css_select),
            (SelectorStrategy.XPATH, SmartSelector._xpath_select),
            (SelectorStrategy.TEXT, SmartSelector._text_select),
            (SelectorStrategy.ARIA, SmartSelector._aria_select),
        ]
        
        for strategy_type, strategy_func in strategies:
            try:
                logger.debug(f"Trying {strategy_type.value} selector: {selector}")
                element = await strategy_func(page, selector, options)
                if element:
                    count = await element.count()
                    if count > 0:
                        logger.success(f"Found element using {strategy_type.value} selector")
                        return element
            except Exception as e:
                logger.debug(f"{strategy_type.value} selector failed: {str(e)}")
                continue
        
        logger.warning(f"Could not find element with any strategy: {selector}")
        return None
    
    @staticmethod
    async def _css_select(page: Page, selector: str, options: SelectorOptions) -> Locator:
        return page.locator(selector)
    
    @staticmethod
    async def _xpath_select(page: Page, selector: str, options: SelectorOptions) -> Locator:
        if not selector.startswith('//') and not selector.startswith('('):
            selector = f"//{selector}"
        return page.locator(f"xpath={selector}")
    
    @staticmethod
    async def _text_select(page: Page, selector: str, options: SelectorOptions) -> Locator:
        return page.get_by_text(selector)
    
    @staticmethod
    async def _aria_select(page: Page, selector: str, options: SelectorOptions) -> Locator:
        return page.get_by_role(selector)
    
    @staticmethod
    async def find_all(
        page: Page,
        selector: str,
        options: Optional[SelectorOptions] = None
    ) -> List[Locator]:
        locator = await SmartSelector.find_element(page, selector, options)
        if locator:
            count = await locator.count()
            return [locator.nth(i) for i in range(count)]
        return []
    
    @staticmethod
    async def safe_click(
        page: Page,
        selector: str,
        options: Optional[SelectorOptions] = None
    ) -> bool:
        try:
            element = await SmartSelector.find_element(page, selector, options)
            if element:
                await element.first.click(timeout=options.timeout if options else 10000)
                logger.success(f"Clicked element: {selector}")
                return True
        except Exception as e:
            logger.error(f"Failed to click element {selector}: {str(e)}")
        return False
    
    @staticmethod
    async def safe_fill(
        page: Page,
        selector: str,
        value: str,
        options: Optional[SelectorOptions] = None
    ) -> bool:
        try:
            element = await SmartSelector.find_element(page, selector, options)
            if element:
                await element.first.fill(value, timeout=options.timeout if options else 10000)
                logger.success(f"Filled element {selector} with value")
                return True
        except Exception as e:
            logger.error(f"Failed to fill element {selector}: {str(e)}")
        return False
    
    @staticmethod
    async def get_text(
        page: Page,
        selector: str,
        options: Optional[SelectorOptions] = None
    ) -> Optional[str]:
        try:
            element = await SmartSelector.find_element(page, selector, options)
            if element:
                text = await element.first.text_content(timeout=options.timeout if options else 10000)
                return text
        except Exception as e:
            logger.error(f"Failed to get text from {selector}: {str(e)}")
        return None
    
    @staticmethod
    async def get_attribute(
        page: Page,
        selector: str,
        attribute: str,
        options: Optional[SelectorOptions] = None
    ) -> Optional[str]:
        try:
            element = await SmartSelector.find_element(page, selector, options)
            if element:
                attr_value = await element.first.get_attribute(attribute, timeout=options.timeout if options else 10000)
                return attr_value
        except Exception as e:
            logger.error(f"Failed to get attribute {attribute} from {selector}: {str(e)}")
        return None
