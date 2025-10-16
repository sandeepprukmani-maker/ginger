#!/usr/bin/env node
/**
 * Playwright MCP Server CLI
 */

const { program } = require('playwright-core/lib/utilsBundle');
const { decorateCommand } = require('playwright/lib/mcp/program');
const packageJSON = require('./package.json');

const p = program.version('Version ' + packageJSON.version).name('Playwright MCP');
decorateCommand(p, packageJSON.version);

void program.parseAsync(process.argv);
