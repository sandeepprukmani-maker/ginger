import asyncio
import logging
import time
from typing import Dict, Any, Optional
from app.services.browser_use_service import BrowserUseService
from app.services.mcp_service import MCPServerService
from app.models.database import DatabaseManager, ActionLog, HealingEvent, Task
from datetime import datetime

logger = logging.getLogger(__name__)

class HealingOrchestrator:
    def __init__(self, config: Dict[str, Any], db_manager: DatabaseManager):
        self.config = config
        self.db_manager = db_manager
        self.browser_use_service = BrowserUseService(config.get('browser', {}))
        self.mcp_service = MCPServerService(config.get('mcp', {}))
        self.healing_config = config.get('healing', {})
    
    async def execute_with_healing(self, task_id: int, instruction: str, emit_callback=None) -> Dict[str, Any]:
        """Execute instruction with automatic healing on failures"""
        try:
            session = self.db_manager.get_session()
            task = session.query(Task).filter_by(id=task_id).first()
            
            if not task:
                return {'success': False, 'error': 'Task not found'}
            
            task.status = 'running'
            task.started_at = datetime.utcnow()
            session.commit()
            
            if emit_callback:
                emit_callback('task_update', task.to_dict())
            
            logger.info(f"Starting execution of task {task_id}: {instruction}")
            
            await self.browser_use_service.initialize()
            
            start_time = time.time()
            result = await self.browser_use_service.execute_task(instruction)
            execution_time = time.time() - start_time
            
            action_log = ActionLog(
                task_id=task_id,
                step_number=1,
                action_type='execute_instruction',
                status='success' if result['success'] else 'failed',
                error_message=result.get('error'),
                execution_time=execution_time,
                locator={'type': 'natural_language', 'value': instruction},
                healing_attempted=False
            )
            session.add(action_log)
            session.commit()
            
            if emit_callback:
                emit_callback('step_update', action_log.to_dict())
            
            if result['success']:
                task.status = 'completed'
                task.completed_at = datetime.utcnow()
                task.successful_steps = 1
                task.total_steps = 1
            else:
                logger.warning(f"Initial execution failed, attempting healing: {result.get('error')}")
                
                healing_result = await self._attempt_healing_flow(
                    task_id=task_id,
                    instruction=instruction,
                    original_error=result.get('error', 'Unknown error'),
                    emit_callback=emit_callback
                )
                
                if healing_result['success']:
                    task.status = 'completed'
                    task.completed_at = datetime.utcnow()
                    task.healed_steps = 1
                    task.successful_steps = 1
                    task.total_steps = 1
                    result = healing_result
                else:
                    task.status = 'failed'
                    task.completed_at = datetime.utcnow()
                    task.failed_steps = 1
                    task.total_steps = 1
                    task.error_message = healing_result.get('error')
            
            session.commit()
            
            if emit_callback:
                emit_callback('task_update', task.to_dict())
            
            await self.browser_use_service.close()
            
            return result
            
        except Exception as e:
            logger.error(f"Error in execute_with_healing: {e}")
            try:
                session = self.db_manager.get_session()
                task = session.query(Task).filter_by(id=task_id).first()
                if task:
                    task.status = 'failed'
                    task.error_message = str(e)
                    task.completed_at = datetime.utcnow()
                    session.commit()
            except Exception as db_error:
                logger.error(f"Error updating task status: {db_error}")
            finally:
                try:
                    self.db_manager.close_session()
                except:
                    pass
            
            return {'success': False, 'error': str(e)}
    
    async def _attempt_healing_flow(self, task_id: int, instruction: str, original_error: str, emit_callback=None) -> Dict[str, Any]:
        """Attempt to heal failed execution using browser-use first, then MCP"""
        logger.info(f"Starting healing flow for task {task_id}")
        
        session = self.db_manager.get_session()
        
        action_log = session.query(ActionLog).filter_by(task_id=task_id, step_number=1).first()
        
        if action_log:
            action_log.healing_attempted = True
            action_log.status = 'healing'
            session.commit()
            action_log_id = action_log.id
        else:
            action_log = ActionLog(
                task_id=task_id,
                step_number=1,
                action_type='execute_instruction',
                status='healing',
                error_message=original_error,
                healing_attempted=True,
                retry_count=0
            )
            session.add(action_log)
            session.commit()
            action_log_id = action_log.id
        
        if emit_callback:
            emit_callback('step_update', action_log.to_dict())
        
        browser_use_retries = self.healing_config.get('browser_use_retry_limit', 2)
        for retry in range(browser_use_retries):
            logger.info(f"Attempting browser-use healing, retry {retry + 1}/{browser_use_retries}")
            
            if emit_callback:
                emit_callback('healing_attempt', {
                    'task_id': task_id,
                    'source': 'browser-use',
                    'retry': retry + 1,
                    'max_retries': browser_use_retries
                })
            
            start_time = time.time()
            result = await self.browser_use_service.execute_task(instruction)
            healing_time = time.time() - start_time
            
            healing_event = HealingEvent(
                action_log_id=action_log_id,
                task_id=task_id,
                healing_source='browser-use',
                original_locator={'type': 'instruction', 'value': instruction},
                healed_locator={'type': 'retry', 'value': f'attempt_{retry + 1}'},
                success=result['success'],
                error_message=result.get('error'),
                healing_time=healing_time
            )
            session.add(healing_event)
            session.commit()
            
            if emit_callback:
                emit_callback('healing_event', healing_event.to_dict())
            
            if result['success']:
                logger.info(f"Browser-use healing successful on retry {retry + 1}")
                
                action_log.status = 'healed'
                action_log.healing_source = 'browser-use'
                action_log.retry_count = retry + 1
                session.commit()
                
                if emit_callback:
                    emit_callback('step_update', action_log.to_dict())
                
                return result
            
            await asyncio.sleep(1)
        
        logger.info("Browser-use healing failed, attempting MCP healing")
        
        if emit_callback:
            emit_callback('healing_fallback', {
                'task_id': task_id,
                'from': 'browser-use',
                'to': 'mcp'
            })
        
        mcp_result = await self._heal_with_mcp(
            task_id=task_id,
            action_log_id=action_log_id,
            instruction=instruction,
            emit_callback=emit_callback
        )
        
        if mcp_result['success']:
            action_log.status = 'healed'
            action_log.healing_source = 'mcp'
            session.commit()
            
            if emit_callback:
                emit_callback('step_update', action_log.to_dict())
        else:
            action_log.status = 'failed'
            session.commit()
            
            if emit_callback:
                emit_callback('step_update', action_log.to_dict())
        
        self.db_manager.close_session()
        return mcp_result
    
    async def _heal_with_mcp(self, task_id: int, action_log_id: int, instruction: str, emit_callback=None) -> Dict[str, Any]:
        """Attempt healing using Microsoft Playwright MCP server"""
        try:
            session = self.db_manager.get_session()
            
            if not self.mcp_service.start_server():
                return {'success': False, 'error': 'Failed to start MCP server'}
            
            mcp_retries = self.healing_config.get('mcp_retry_limit', 2)
            
            for retry in range(mcp_retries):
                logger.info(f"Attempting MCP healing, retry {retry + 1}/{mcp_retries}")
                
                if emit_callback:
                    emit_callback('healing_attempt', {
                        'task_id': task_id,
                        'source': 'mcp',
                        'retry': retry + 1,
                        'max_retries': mcp_retries
                    })
                
                start_time = time.time()
                
                success = await self._execute_instruction_with_mcp(instruction, action_log_id)
                
                healing_time = time.time() - start_time
                
                healing_event = HealingEvent(
                    action_log_id=action_log_id,
                    task_id=task_id,
                    healing_source='mcp',
                    original_locator={'type': 'instruction', 'value': instruction},
                    healed_locator={'type': 'mcp_execution', 'value': f'attempt_{retry + 1}'},
                    success=success,
                    error_message=None if success else 'MCP execution failed',
                    healing_time=healing_time
                )
                session.add(healing_event)
                session.commit()
                
                if emit_callback:
                    emit_callback('healing_event', healing_event.to_dict())
                
                if success:
                    logger.info(f"MCP healing successful on retry {retry + 1}")
                    self.db_manager.close_session()
                    return {
                        'success': True,
                        'result': 'Healed via MCP',
                        'healing_source': 'mcp',
                        'execution_time': healing_time
                    }
                
                await asyncio.sleep(1)
            
            self.db_manager.close_session()
            return {'success': False, 'error': 'MCP healing failed after all retries'}
            
        except Exception as e:
            logger.error(f"Error in MCP healing: {e}")
            return {'success': False, 'error': str(e)}
        finally:
            self.mcp_service.stop_server()
    
    async def _execute_instruction_with_mcp(self, instruction: str, action_log_id: Optional[int] = None) -> bool:
        """Execute instruction using MCP commands with selector discovery"""
        session = None
        try:
            instruction_lower = instruction.lower()
            session = self.db_manager.get_session() if action_log_id else None
            
            # Handle navigation
            if 'go to' in instruction_lower or 'navigate' in instruction_lower:
                url_start = instruction_lower.find('http')
                if url_start == -1:
                    url_start = instruction_lower.find('www.')
                
                if url_start != -1:
                    url = instruction[url_start:].split()[0]
                    result = self.mcp_service.navigate(url)
                    if session and action_log_id and result:
                        action_log = session.query(ActionLog).filter_by(id=action_log_id).first()
                        if action_log:
                            action_log.healed_locator = {'type': 'url', 'value': url}
                            session.commit()
                    return result
            
            # Handle click actions
            elif 'click' in instruction_lower:
                # Extract target description
                target = instruction_lower.split('click')[-1].strip()
                if target.startswith('on '):
                    target = target[3:].strip()
                
                # Get element locator
                selector = self.mcp_service.get_element_locator(target)
                if selector:
                    logger.info(f"MCP discovered selector for click: {selector}")
                    result = self.mcp_service.click_element(selector)
                    
                    # Store healed selector in ActionLog
                    if session and action_log_id and result:
                        action_log = session.query(ActionLog).filter_by(id=action_log_id).first()
                        if action_log:
                            action_log.healed_locator = {'type': 'css', 'selector': selector}
                            action_log.original_locator = action_log.locator
                            session.commit()
                    
                    return result
            
            # Handle fill/type actions
            elif 'fill' in instruction_lower or 'type' in instruction_lower or 'enter' in instruction_lower:
                # Extract target description and value to fill
                # IMPORTANT: Use instruction_lower for pattern matching, but extract from original instruction to preserve casing
                target_desc = ""
                value_to_fill = ""
                
                # Parse instruction to extract field description and value
                # Common patterns: "fill [field] with [value]", "type [value] in [field]", "enter [value] in [field]"
                if ' with ' in instruction_lower:
                    # Pattern: "fill [field] with [value]"
                    # Find the position in original string
                    with_pos = instruction_lower.find(' with ')
                    if with_pos != -1:
                        field_part = instruction[:with_pos]
                        value_part = instruction[with_pos + 6:]  # 6 = len(' with ')
                        
                        # Extract target description (lowercase for matching)
                        target_desc = field_part.lower().replace('fill', '').replace('type', '').strip()
                        # Extract value (preserve original case, remove quotes)
                        value_to_fill = value_part.strip().strip('"').strip("'")
                        
                elif ' in ' in instruction_lower:
                    # Pattern: "type [value] in [field]" or "enter [value] in [field]"
                    # Find the position in original string
                    in_pos = instruction_lower.find(' in ')
                    if in_pos != -1:
                        value_part = instruction[:in_pos]
                        field_part = instruction[in_pos + 4:]  # 4 = len(' in ')
                        
                        # Extract target description (lowercase for matching)
                        target_desc = field_part.strip().lower()
                        # Extract value: remove only the leading command word using regex
                        import re
                        # Remove leading "fill", "type", "enter", etc. (case-insensitive, only at start)
                        value_cleaned = re.sub(r'^\s*(fill|type|enter)\s+', '', value_part, count=1, flags=re.IGNORECASE)
                        value_to_fill = value_cleaned.strip().strip('"').strip("'")
                        
                else:
                    # Fallback: try to extract from original instruction using regex
                    target_desc = "input field"
                    # Try to extract quoted value from original instruction
                    import re
                    quoted = re.findall(r'"([^"]+)"|\'([^\']+)\'', instruction)
                    if quoted:
                        value_to_fill = quoted[0][0] or quoted[0][1]
                
                if not target_desc:
                    target_desc = "input field"
                
                # Get element locator
                selector = self.mcp_service.get_element_locator(target_desc)
                if selector:
                    logger.info(f"MCP discovered selector for fill: {selector}, value: {value_to_fill}")
                    
                    # Actually perform the fill action
                    if value_to_fill:
                        result = self.mcp_service.fill_input(selector, value_to_fill)
                    else:
                        # No value extracted, just verify element exists
                        logger.warning(f"No value extracted from instruction: {instruction}")
                        result = False
                    
                    # Store healed selector in ActionLog only if fill succeeded
                    if session and action_log_id and result:
                        action_log = session.query(ActionLog).filter_by(id=action_log_id).first()
                        if action_log:
                            action_log.healed_locator = {'type': 'css', 'selector': selector, 'value': value_to_fill}
                            action_log.original_locator = action_log.locator
                            session.commit()
                    
                    return result
                else:
                    logger.warning(f"Could not find selector for: {target_desc}")
                    return False
            
            # Handle search actions
            elif 'search' in instruction_lower:
                target_desc = "search input or search field"
                selector = self.mcp_service.get_element_locator(target_desc)
                if selector:
                    logger.info(f"MCP discovered selector for search: {selector}")
                    
                    if session and action_log_id:
                        action_log = session.query(ActionLog).filter_by(id=action_log_id).first()
                        if action_log:
                            action_log.healed_locator = {'type': 'css', 'selector': selector}
                            action_log.original_locator = action_log.locator
                            session.commit()
                    
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error executing instruction with MCP: {e}")
            return False
        finally:
            if session:
                self.db_manager.close_session()
