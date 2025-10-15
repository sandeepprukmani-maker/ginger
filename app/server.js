const express = require('express');
const cors = require('cors');
const OpenAI = require('openai');
const { Client } = require('@modelcontextprotocol/sdk/client/index.js');
const { SSEClientTransport } = require('@modelcontextprotocol/sdk/client/sse.js');

const app = express();
app.use(cors());
app.use(express.json());
app.use(express.static('app/public'));

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY
});

let mcpClient = null;
let availableTools = [];

async function connectToMCP() {
  if (mcpClient) return mcpClient;

  try {
    const transport = new SSEClientTransport(
      new URL('http://localhost:8080/sse')
    );
    
    mcpClient = new Client({
      name: 'browser-automation-app',
      version: '1.0.0'
    }, {
      capabilities: {}
    });

    await mcpClient.connect(transport);
    
    const toolsResult = await mcpClient.listTools();
    availableTools = toolsResult.tools || [];
    
    console.log(`Connected to MCP server. Available tools: ${availableTools.length}`);
    return mcpClient;
  } catch (error) {
    console.error('Failed to connect to MCP:', error);
    throw error;
  }
}

app.post('/api/automate', async (req, res) => {
  const { command } = req.body;
  
  if (!command) {
    return res.status(400).json({ error: 'Command is required' });
  }

  try {
    const client = await connectToMCP();
    
    const toolDescriptions = availableTools.map(tool => ({
      type: 'function',
      function: {
        name: tool.name,
        description: tool.description,
        parameters: tool.inputSchema
      }
    }));

    const messages = [
      {
        role: 'system',
        content: `You are a browser automation assistant. The user will give you instructions in natural language, and you need to use the available Playwright browser tools to accomplish the task. 
        
Execute the steps in order. For navigation, use browser_navigate. For clicking elements, use browser_click with the exact ref from the snapshot. For typing, use browser_type.

Important: Always call browser_snapshot first to see the current page state before interacting with elements.`
      },
      {
        role: 'user',
        content: command
      }
    ];

    const steps = [];
    let conversationMessages = [...messages];
    let maxIterations = 15;
    let iteration = 0;

    while (iteration < maxIterations) {
      iteration++;
      
      const completion = await openai.chat.completions.create({
        model: 'gpt-4o',
        messages: conversationMessages,
        tools: toolDescriptions,
        tool_choice: 'auto'
      });

      const assistantMessage = completion.choices[0].message;
      conversationMessages.push(assistantMessage);

      if (!assistantMessage.tool_calls || assistantMessage.tool_calls.length === 0) {
        steps.push({
          type: 'completion',
          content: assistantMessage.content || 'Task completed'
        });
        break;
      }

      for (const toolCall of assistantMessage.tool_calls) {
        const toolName = toolCall.function.name;
        const toolArgs = JSON.parse(toolCall.function.arguments);

        steps.push({
          type: 'tool_call',
          tool: toolName,
          arguments: toolArgs
        });

        try {
          const result = await client.callTool({
            name: toolName,
            arguments: toolArgs
          });

          const resultContent = result.content
            .map(c => c.type === 'text' ? c.text : '[non-text content]')
            .join('\n');

          steps.push({
            type: 'tool_result',
            tool: toolName,
            result: resultContent.substring(0, 500)
          });

          conversationMessages.push({
            role: 'tool',
            tool_call_id: toolCall.id,
            content: resultContent
          });
        } catch (error) {
          const errorMsg = error.message || String(error);
          steps.push({
            type: 'error',
            tool: toolName,
            error: errorMsg
          });

          conversationMessages.push({
            role: 'tool',
            tool_call_id: toolCall.id,
            content: `Error: ${errorMsg}`
          });
        }
      }
    }

    res.json({ success: true, steps });
  } catch (error) {
    console.error('Automation error:', error);
    res.status(500).json({ 
      error: error.message || 'Failed to execute automation',
      details: error.toString()
    });
  }
});

app.get('/api/status', async (req, res) => {
  try {
    await connectToMCP();
    res.json({ 
      status: 'connected',
      tools: availableTools.length,
      toolNames: availableTools.slice(0, 10).map(t => t.name)
    });
  } catch (error) {
    res.json({ 
      status: 'disconnected',
      error: error.message 
    });
  }
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, '0.0.0.0', () => {
  console.log(`Browser Automation App running on port ${PORT}`);
  connectToMCP().catch(err => {
    console.error('Initial MCP connection failed:', err.message);
  });
});
