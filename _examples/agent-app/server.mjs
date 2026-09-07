import http from 'node:http';
import { Pool } from 'pg';
if (!process.env.DATABASE_URL) throw new Error('Set DATABASE_URL');
const pool = new Pool({ connectionString: process.env.DATABASE_URL, max: 2, connectionTimeoutMillis: 5000 });
await pool.query('CREATE TABLE IF NOT EXISTS docs_probe (id text PRIMARY KEY, value text NOT NULL)');
await pool.query("INSERT INTO docs_probe VALUES ('example', 'database-connected') ON CONFLICT (id) DO NOTHING");
const server = http.createServer(async (req, res) => {
  if (req.method !== 'GET' || !['/', '/health', '/data'].includes(req.url)) {
    res.writeHead(404).end('Not found'); return;
  }
  try {
    if (req.url === '/data') {
      const result = await pool.query("SELECT value FROM docs_probe WHERE id = 'example'");
      res.writeHead(200, { 'content-type': 'application/json' }).end(JSON.stringify(result.rows[0]));
    } else res.writeHead(200, { 'content-type': 'text/plain' }).end('App ready');
  } catch { res.writeHead(503).end('Database unavailable'); }
});
server.listen(Number(process.env.PORT || 3000), '0.0.0.0', () => console.log('App ready'));
process.on('SIGTERM', () => server.close(async () => { await pool.end(); }));
