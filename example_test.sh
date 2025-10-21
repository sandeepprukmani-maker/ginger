#!/bin/bash

echo "╔══════════════════════════════════════════════════════════╗"
echo "║      Playwright MCP CLI - Example Demonstration         ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "This example demonstrates the CLI tool capabilities."
echo ""
echo "To run the CLI interactively:"
echo "  python main.py --interactive"
echo ""
echo "To run with a direct command:"
echo "  python main.py 'Go to example.com and click More Information'"
echo ""
echo "To get help:"
echo "  python main.py --help"
echo ""
echo "Generated scripts will be saved to: generated_scripts/"
echo ""
echo "Press Ctrl+C to exit"
echo ""

python main.py --help
