"""Export code-use session to Jupyter notebook format."""

import json
from pathlib import Path

from .views import CellType, NotebookExport, NotebookSession


def export_to_ipynb(session: NotebookSession, output_path: str | Path) -> Path:
	"""
	Export a NotebookSession to a Jupyter notebook (.ipynb) file.

	Args:
		session: The NotebookSession to export
		output_path: Path where to save the notebook file

	Returns:
		Path to the saved notebook file

	Example:
		```python
	        session = await agent.run()
	        notebook_path = export_to_ipynb(session, 'my_automation.ipynb')
	        print(f'Notebook saved to {notebook_path}')
		```
	"""
	output_path = Path(output_path)

	# Create notebook structure
	notebook = NotebookExport(
		metadata={
			'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'},
			'language_info': {
				'name': 'python',
				'version': '3.11.0',
				'mimetype': 'text/x-python',
				'codemirror_mode': {'name': 'ipython', 'version': 3},
				'pygments_lexer': 'ipython3',
				'nbconvert_exporter': 'python',
				'file_extension': '.py',
			},
		}
	)

	# Add setup cell at the beginning with proper type hints
	setup_code = """import asyncio
from typing import Any
from browser_use import BrowserSession
from browser_use.code_use import create_namespace

# Initialize browser and namespace
browser = BrowserSession()
await browser.start()

# Create namespace with all browser control functions
namespace: dict[str, Any] = create_namespace(browser)

# Import all functions into the current namespace
globals().update(namespace)

# Type hints for better IDE support (these are now available globally)
# navigate, click, input, evaluate, search, extract, scroll, done, etc.

print("Browser-use environment initialized!")
print("Available functions: navigate, click, input, evaluate, search, extract, done, etc.")"""

	setup_cell = {
		'cell_type': 'code',
		'metadata': {},
		'source': setup_code.split('\n'),
		'execution_count': None,
		'outputs': [],
	}
	notebook.cells.append(setup_cell)

	# Convert cells
	for cell in session.cells:
		notebook_cell: dict = {
			'cell_type': cell.cell_type.value,
			'metadata': {},
			'source': cell.source.splitlines(keepends=True),
		}

		if cell.cell_type == CellType.CODE:
			notebook_cell['execution_count'] = cell.execution_count
			notebook_cell['outputs'] = []

			# Add output if available
			if cell.output:
				notebook_cell['outputs'].append(
					{
						'output_type': 'stream',
						'name': 'stdout',
						'text': cell.output.split('\n'),
					}
				)

			# Add error if available
			if cell.error:
				notebook_cell['outputs'].append(
					{
						'output_type': 'error',
						'ename': 'Error',
						'evalue': cell.error.split('\n')[0] if cell.error else '',
						'traceback': cell.error.split('\n') if cell.error else [],
					}
				)

			# Add browser state as a separate output
			if cell.browser_state:
				notebook_cell['outputs'].append(
					{
						'output_type': 'stream',
						'name': 'stdout',
						'text': [f'Browser State:\n{cell.browser_state}'],
					}
				)

		notebook.cells.append(notebook_cell)

	# Write to file
	output_path.parent.mkdir(parents=True, exist_ok=True)
	with open(output_path, 'w', encoding='utf-8') as f:
		json.dump(notebook.model_dump(), f, indent=2, ensure_ascii=False)

	return output_path


def session_to_python_script(session: NotebookSession) -> str:
	"""
	Convert a NotebookSession to a Python script.

	Args:
		session: The NotebookSession to convert

	Returns:
		Python script as a string

	Example:
		```python
	        session = await agent.run()
	        script = session_to_python_script(session)
	        print(script)
		```
	"""
	lines = []

	lines.append('# Generated from browser-use code-use session\n')
	lines.append('import asyncio\n')
	lines.append('from browser_use import BrowserSession\n')
	lines.append('from browser_use.code_use import create_namespace\n\n')

	lines.append('async def main():\n')
	lines.append('\t# Initialize browser and namespace\n')
	lines.append('\tbrowser = BrowserSession()\n')
	lines.append('\tawait browser.start()\n\n')
	lines.append('\t# Create namespace with all browser control functions\n')
	lines.append('\tnamespace = create_namespace(browser)\n\n')
	lines.append('\t# Extract functions from namespace for direct access\n')
	lines.append('\tnavigate = namespace["navigate"]\n')
	lines.append('\tclick = namespace["click"]\n')
	lines.append('\tinput_text = namespace["input"]\n')
	lines.append('\tevaluate = namespace["evaluate"]\n')
	lines.append('\tsearch = namespace["search"]\n')
	lines.append('\textract = namespace["extract"]\n')
	lines.append('\tscroll = namespace["scroll"]\n')
	lines.append('\tdone = namespace["done"]\n')
	lines.append('\tgo_back = namespace["go_back"]\n')
	lines.append('\twait = namespace["wait"]\n')
	lines.append('\tscreenshot = namespace["screenshot"]\n')
	lines.append('\tfind_text = namespace["find_text"]\n')
	lines.append('\tswitch_tab = namespace["switch"]\n')
	lines.append('\tclose_tab = namespace["close"]\n')
	lines.append('\tdropdown_options = namespace["dropdown_options"]\n')
	lines.append('\tselect_dropdown = namespace["select_dropdown"]\n')
	lines.append('\tupload_file = namespace["upload_file"]\n')
	lines.append('\tsend_keys = namespace["send_keys"]\n\n')

	for i, cell in enumerate(session.cells):
		if cell.cell_type == CellType.CODE:
			lines.append(f'\t# Cell {i + 1}\n')

			# Indent each line of source
			source_lines = cell.source.split('\n')
			for line in source_lines:
				if line.strip():  # Only add non-empty lines
					lines.append(f'\t{line}\n')

			lines.append('\n')

	lines.append('\tawait browser.stop()\n\n')
	lines.append("if __name__ == '__main__':\n")
	lines.append('\tasyncio.run(main())\n')

	return ''.join(lines)
