import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import assert from 'node:assert/strict';
import { StreamableHTTPClientTransport } from '@modelcontextprotocol/sdk/client/streamableHttp.js';
if (!process.env.MCP_URL || !process.env.MCP_TOKEN) throw new Error('Set MCP_URL and MCP_TOKEN');
const endpoint = new URL(process.env.MCP_URL);
const authorization = { Authorization: `Bearer ${process.env.MCP_TOKEN}` };
assert.equal((await fetch(new URL('/health', endpoint))).status, 200);
assert.equal((await fetch(endpoint, { method: 'POST' })).status, 401);
assert.equal((await fetch(endpoint, { method: 'POST', headers: { Authorization: 'Bearer invalid' } })).status, 401);
assert.equal((await fetch(endpoint, { headers: authorization })).status, 405);
assert.equal((await fetch(endpoint, { method: 'POST', headers: { ...authorization, Origin: 'https://untrusted.example' } })).status, 403);
console.log('HTTPS/HTTP health, missing/invalid token, method and origin checks passed');
const client = new Client({ name: 'arithmetic-client', version: '1.0.0' });
try {
  await client.connect(new StreamableHTTPClientTransport(new URL(process.env.MCP_URL), {
    requestInit: { headers: { Authorization: `Bearer ${process.env.MCP_TOKEN}` } },
  }));
  assert.ok((await client.listTools()).tools.some(tool => tool.name === 'add'));
  const result = await client.callTool({ name: 'add', arguments: { a: 2, b: 3 } });
  assert.notEqual(result.isError, true);
  assert.deepEqual(result.content, [{ type: 'text', text: '5' }]);
  console.log('MCP initialize, tools/list and tools/call passed: 5');
} finally {
  await client.close();
}
