import express from 'express';
import { importSPKI, jwtVerify } from 'jose';
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';
import { z } from 'zod';

export async function createApp({ publicKey, allowedHosts }) {
  const key = await importSPKI(publicKey, 'RS256');
  const hosts = new Set(allowedHosts);
  const app = express();
  app.use((req, res, next) => {
    if (!hosts.has(req.hostname)) return res.status(403).send('Host not allowed');
    // This example accepts server clients; it does not enable browser origins.
    if (req.headers.origin) return res.status(403).send('Browser origin not allowed');
    next();
  });
  app.get('/health', (_req, res) => res.type('text').send('ok'));
  app.use('/mcp', async (req, res, next) => {
    const match = /^Bearer (.+)$/.exec(req.headers.authorization ?? '');
    if (!match) return res.status(401).send('Bearer token required');
    try {
      await jwtVerify(match[1], key, {
        issuer: 'mcp-example', audience: 'mcp-example',
        algorithms: ['RS256'], requiredClaims: ['exp', 'iss', 'aud'],
      });
      next();
    } catch {
      res.status(401).send('Invalid bearer token');
    }
  });
  app.use(express.json({ limit: '64kb' }));
  app.post('/mcp', async (req, res) => {
    const server = new McpServer({ name: 'arithmetic', version: '1.0.0' });
    server.registerTool('add', {
      description: 'Add two integers',
      inputSchema: { a: z.number().int(), b: z.number().int() },
    }, async ({ a, b }) => ({ content: [{ type: 'text', text: String(a + b) }] }));
    const transport = new StreamableHTTPServerTransport({ sessionIdGenerator: undefined });
    res.on('close', () => { void transport.close(); void server.close(); });
    try {
      await server.connect(transport);
      await transport.handleRequest(req, res, req.body);
    } catch {
      if (!res.headersSent) res.status(500).json({ error: 'MCP request failed' });
    }
  });
  app.all('/mcp', (_req, res) => res.status(405).set('Allow', 'POST').send('Use POST'));
  return app;
}

if (process.argv[1] === new URL(import.meta.url).pathname) {
  const publicKey = process.env.MCP_PUBLIC_KEY;
  const allowedHosts = process.env.MCP_ALLOWED_HOSTS?.split(',').map(s => s.trim()).filter(Boolean);
  if (!publicKey || !allowedHosts?.length) throw new Error('Set MCP_PUBLIC_KEY and MCP_ALLOWED_HOSTS');
  const app = await createApp({ publicKey, allowedHosts });
  const server = app.listen(Number(process.env.PORT || 8000), '0.0.0.0', () => console.log('MCP server ready'));
  process.on('SIGTERM', () => server.close());
}
