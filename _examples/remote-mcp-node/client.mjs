import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StreamableHTTPClientTransport } from '@modelcontextprotocol/sdk/client/streamableHttp.js';
if (!process.env.MCP_URL || !process.env.MCP_TOKEN) throw new Error('Set MCP_URL and MCP_TOKEN');
const client = new Client({ name: 'arithmetic-client', version: '1.0.0' });
try {
  await client.connect(new StreamableHTTPClientTransport(new URL(process.env.MCP_URL), {
    requestInit: { headers: { Authorization: `Bearer ${process.env.MCP_TOKEN}` } },
  }));
  console.log((await client.callTool({ name: 'add', arguments: { a: 2, b: 3 } })).content);
} finally {
  await client.close();
}
