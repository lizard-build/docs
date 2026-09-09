import { db } from '../../lib/db.js';
import { randomUUID } from 'node:crypto';
const instanceId = randomUUID();
export const dynamic = 'force-dynamic';
export const runtime = 'nodejs';
export async function GET() {
  try {
    await db().query('SELECT id FROM notes LIMIT 1');
    return Response.json({ ready: true, instanceId }, { headers: { 'Cache-Control': 'no-store' } });
  } catch {
    return Response.json({ ready: false }, { status: 503, headers: { 'Cache-Control': 'no-store' } });
  }
}
