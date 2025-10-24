# Browser-Use Engine Optimizations

## Overview

The browser-use engine has been significantly optimized with advanced features for handling both basic and complex browser automation tasks. This document outlines all the enhancements and how to use them.

## New Features

### 1. Advanced Browser Capabilities (`advanced_features.py`)

**Features:**
- **Screenshot Capture**: Full-page and viewport screenshots with custom naming
- **PDF Generation**: Convert pages to PDF with customizable settings
- **Cookie Management**: Save and restore browser sessions
- **LocalStorage Management**: Read and write localStorage data
- **Session Persistence**: Maintain authentication across automation runs

**Usage:**
```python
from browser_use_codebase.advanced_features import AdvancedBrowserFeatures

features = AdvancedBrowserFeatures(output_dir="automation_outputs")

# Capture screenshot
await features.capture_screenshot(page, name="login_page", full_page=True)

# Generate PDF
await features.generate_pdf(page, name="report", landscape=False)

# Save cookies for session persistence
await features.save_cookies(context, session_name="user_session")

# Restore cookies
await features.load_cookies(context, session_name="user_session")
```

### 2. Enhanced Popup Handling (`popup_handler.py`)

**Improvements:**
- Configurable timeouts for popup operations
- Detailed logging and tracking of all popups
- Popup history and statistics
- Multi-popup orchestration
- Automatic or manual popup switching

**Configuration (config.ini):**
```ini
[popup]
timeout = 10000          # Timeout in milliseconds
auto_switch = true       # Auto-switch to new popups
log_verbose = true       # Enable detailed logging
```

**Features:**
- Tracks total popups opened during session
- Records popup URLs and timestamps
- Provides statistics via `get_popup_stats()`
- Waits for popups with `wait_for_popup(timeout)`

### 3. Smart Retry Mechanism (`retry_mechanism.py`)

**Features:**
- Exponential backoff for failed operations
- Configurable retry attempts and delays
- Separate retry configs for different operation types
- Retry statistics and success rate tracking
- Support for both sync and async operations

**Configuration (config.ini):**
```ini
[retry]
max_retries = 3          # Maximum retry attempts
initial_delay = 1.0      # Initial delay in seconds
max_delay = 30.0         # Maximum delay between retries
backoff_factor = 2.0     # Exponential backoff multiplier
```

**Usage:**
```python
from browser_use_codebase.retry_mechanism import create_retry_mechanism

retry = create_retry_mechanism(max_retries=3, initial_delay=1.0)

# Decorate sync functions
@retry.retry
def unreliable_operation():
    # Operation that might fail
    pass

# Decorate async functions
@retry.async_retry
async def async_unreliable_operation():
    # Async operation that might fail
    pass
```

### 4. Workflow State Management (`state_manager.py`)

**Features:**
- Preserve context across multi-step workflows
- Variable storage and retrieval
- Execution history tracking
- Checkpoint creation and restoration
- Optional disk persistence for recovery

**Usage:**
```python
from browser_use_codebase.state_manager import WorkflowState

# Create workflow state
state = WorkflowState(workflow_id="data_collection", persist_to_disk=True)

# Store variables
state.set_variable("user_email", "user@example.com")
state.set_state("current_page", "login")

# Record steps
state.add_step("login", {"success": True, "url": "https://example.com"})

# Create checkpoints
state.create_checkpoint("after_login")

# Restore if needed
state.restore_checkpoint("after_login")

# Get summary
summary = state.get_summary()
```

### 5. Data Extraction Capabilities (`data_extractor.py`)

**Features:**
- Table data extraction with headers
- List extraction with custom selectors
- Structured data extraction using schemas
- Link and image extraction
- Page metadata extraction
- Text content extraction

**Usage:**
```python
from browser_use_codebase.data_extractor import DataExtractor

extractor = DataExtractor()

# Extract table data
table_data = await extractor.extract_table(page, selector="table", include_headers=True)

# Extract structured data
schema = {
    "title": "h1.product-title",
    "price": "span.price",
    "description": "div.description"
}
data = await extractor.extract_structured_data(page, schema)

# Extract all links
links = await extractor.extract_all_links(page)

# Extract page metadata
metadata = await extractor.extract_metadata(page)
```

### 6. Performance Monitoring (`performance_monitor.py`)

**Features:**
- Operation timing and duration tracking
- Success rate calculation
- Per-operation metrics and breakdown
- Custom metric recording
- Detailed performance summaries

**Configuration (config.ini):**
```ini
[performance]
track_detailed_metrics = true    # Track detailed per-operation metrics
log_summary = true               # Log summary after completion
```

**Usage:**
```python
from browser_use_codebase.performance_monitor import PerformanceMonitor

monitor = PerformanceMonitor(track_detailed_metrics=True)

# Track operation
op_id = monitor.start_operation("page_navigation")
# ... perform operation ...
monitor.end_operation(op_id, success=True)

# Get summary
summary = monitor.get_summary()

# Get slowest operations
slowest = monitor.get_top_slowest_operations(limit=5)

# Log formatted summary
monitor.log_summary()
```

### 7. Optimized Engine (`engine_optimized.py`)

The new `OptimizedBrowserUseEngine` integrates all advanced features:

**Features:**
- All advanced capabilities enabled by default
- Performance monitoring built-in
- Retry mechanism integrated
- Workflow state management
- Metrics and statistics

**Usage:**
```python
from browser_use_codebase.engine_optimized import OptimizedBrowserUseEngine

# Create optimized engine
engine = OptimizedBrowserUseEngine(
    headless=True, 
    enable_advanced_features=True
)

# Execute with advanced features
result = engine.execute_instruction_sync(
    "Navigate to example.com and extract the page title",
    workflow_id="data_extraction",
    save_screenshot=True,
    save_pdf=False
)

# Access performance metrics
metrics = engine.get_performance_summary()
retry_stats = engine.get_retry_stats()
```

## Configuration

All features can be configured via `config/config.ini`:

```ini
[retry]
max_retries = 3
initial_delay = 1.0
max_delay = 30.0
backoff_factor = 2.0

[popup]
timeout = 10000
auto_switch = true
log_verbose = true

[performance]
track_detailed_metrics = true
log_summary = true

[advanced_features]
enable_screenshots = true
enable_pdf_generation = true
enable_cookie_management = true
enable_state_persistence = true
output_directory = automation_outputs

[data_extraction]
enable_auto_extraction = false
extract_metadata = true
```

## Migration Guide

### From Basic Engine to Optimized Engine

**Before:**
```python
from browser_use_codebase import create_engine

engine = create_engine(headless=True)
result = engine.execute_instruction_sync("Navigate to example.com")
```

**After:**
```python
from browser_use_codebase.engine_optimized import OptimizedBrowserUseEngine

engine = OptimizedBrowserUseEngine(headless=True, enable_advanced_features=True)
result = engine.execute_instruction_sync(
    "Navigate to example.com",
    save_screenshot=True
)

# Access additional metrics
print(result["performance_metrics"])
print(result["retry_stats"])
```

## Performance Improvements

1. **Retry Mechanism**: Automatic retry with exponential backoff reduces failure rate
2. **Performance Monitoring**: Identify slow operations and optimize
3. **State Management**: Checkpoint and resume long-running workflows
4. **Enhanced Popup Handling**: Better timeout management and logging

## Best Practices

1. **Enable Advanced Features for Complex Tasks**: Use `OptimizedBrowserUseEngine` for multi-step workflows
2. **Use State Management for Long Workflows**: Create checkpoints at key stages
3. **Monitor Performance**: Review metrics to identify bottlenecks
4. **Configure Retries**: Adjust retry settings based on operation reliability
5. **Save Sessions**: Use cookie management for authenticated workflows
6. **Extract Data Efficiently**: Use structured extraction with schemas

## Troubleshooting

### High Failure Rate
- Increase `max_retries` in config
- Adjust `initial_delay` and `backoff_factor`
- Check performance metrics for slow operations

### Popup Issues
- Increase `popup.timeout` in config
- Enable `log_verbose` to see detailed popup logs
- Review popup statistics via `get_popup_stats()`

### Performance Issues
- Enable `track_detailed_metrics` to identify slow operations
- Use `get_top_slowest_operations()` to find bottlenecks
- Consider increasing `max_steps` for complex tasks

## Future Enhancements

Planned improvements:
- [ ] Advanced visual element recognition
- [ ] Multi-tab parallel execution
- [ ] Browser fingerprint randomization
- [ ] Proxy rotation support
- [ ] Advanced authentication flow handling
- [ ] Real-time progress streaming
- [ ] Webhook notifications for completed tasks

## API Reference

See individual module docstrings for detailed API documentation:
- `advanced_features.py` - Advanced browser capabilities
- `popup_handler.py` - Popup window handling
- `retry_mechanism.py` - Retry logic and backoff
- `state_manager.py` - Workflow state management
- `data_extractor.py` - Data extraction utilities
- `performance_monitor.py` - Performance tracking
- `engine_optimized.py` - Optimized automation engine
