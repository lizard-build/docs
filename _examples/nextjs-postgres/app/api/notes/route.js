import { db } from '../../../lib/db.js';
import { authorized } from '../../../lib/auth.js';
export const dynamic = 'force-dynamic';
export const runtime = 'nodejs';
const json = (body, status = 200) => Response.json(body, { status, headers: { 'Cache-Control': 'no-store' } });
export async function GET(request) {
  if (!authorized(request)) return json({ error: 'Unauthorized' }, 401);
  try {
    const { rows } = await db().query('SELECT id, body, created_at FROM notes ORDER BY created_at DESC LIMIT 50');
    return json({ notes: rows });
  } catch { return json({ error: 'Database unavailable' }, 503); }
}
export async function POST(request) {
  if (!authorized(request)) return json({ error: 'Unauthorized' }, 401);
  const raw = await request.text();
  if (raw.length > 2048) return json({ error: 'Request too large' }, 413);
  let value;
  try { value = JSON.parse(raw); } catch { return json({ error: 'Invalid JSON' }, 400); }
  if (!value || typeof value.id !== 'string' || !/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(value.id) || typeof value.body !== 'string' || !value.body.trim() || value.body.length > 200) return json({ error: 'Use a UUID v4 id and 1–200 characters of body text' }, 400);
  try {
    const { rows } = await db().query('INSERT INTO notes(id, body) VALUES ($1, $2) ON CONFLICT (id) DO NOTHING RETURNING id, body', [value.id, value.body]);
    return rows.length ? json(rows[0], 201) : json({ error: 'Note ID already exists' }, 409);
  } catch { return json({ error: 'Database unavailable' }, 503); }
}
