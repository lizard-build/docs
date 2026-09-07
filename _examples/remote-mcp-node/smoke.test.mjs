import { test } from 'node:test';
import assert from 'node:assert/strict';
import { request } from 'node:http';
import { generateKeyPair, exportSPKI, SignJWT } from 'jose';
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StreamableHTTPClientTransport } from '@modelcontextprotocol/sdk/client/streamableHttp.js';
import { createApp } from './server.mjs';

test('authenticated HTTP initialize, list and call; reject missing or invalid credentials', async (t) => {
  const { publicKey, privateKey } = await generateKeyPair('RS256', { extractable: true });
  const app = await createApp({ publicKey: await exportSPKI(publicKey), allowedHosts: ['127.0.0.1'] });
  const listener = app.listen(0, '127.0.0.1');
  await new Promise(resolve => listener.once('listening', resolve));
  t.after(() => { listener.closeAllConnections(); listener.close(); });
  const origin = `http://127.0.0.1:${listener.address().port}`;
  const token = await new SignJWT({}).setProtectedHeader({ alg: 'RS256' }).setIssuer('mcp-example').setAudience('mcp-example').setExpirationTime('5m').sign(privateKey);
  assert.equal((await fetch(`${origin}/health`)).status, 200);
  assert.equal((await fetch(`${origin}/mcp`, { method: 'POST' })).status, 401);
  assert.equal((await fetch(`${origin}/mcp`, { method: 'POST', headers: { Authorization: 'Bearer invalid' } })).status, 401);
  const deniedHost = await new Promise((resolve, reject) => {
    const req = request(`${origin}/health`, { headers: { Host: 'untrusted.test' } }, res => { res.resume(); resolve(res.statusCode); });
    req.on('error', reject);
    req.end();
  });
  assert.equal(deniedHost, 403);
  const client = new Client({ name: 'smoke', version: '1.0.0' });
  t.after(() => client.close());
  await client.connect(new StreamableHTTPClientTransport(new URL(`${origin}/mcp`), { requestInit: { headers: { Authorization: `Bearer ${token}` } } }));
  assert.ok((await client.listTools()).tools.some(tool => tool.name === 'add'));
  assert.deepEqual((await client.callTool({ name: 'add', arguments: { a: 2, b: 3 } })).content, [{ type: 'text', text: '5' }]);
});
