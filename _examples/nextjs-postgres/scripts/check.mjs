import assert from 'node:assert/strict';
const { APP_URL, API_TOKEN, NOTE_ID } = process.env;
if (!APP_URL || !API_TOKEN || !NOTE_ID) throw new Error('Set APP_URL, API_TOKEN and NOTE_ID');
const headers = { Authorization: `Bearer ${API_TOKEN}`, 'Content-Type': 'application/json' };
assert.equal((await fetch(`${APP_URL}/health`)).status, 200);
assert.equal((await fetch(`${APP_URL}/api/notes`)).status, 401);
assert.equal((await fetch(`${APP_URL}/missing-check-route`)).status, 404);
if (process.argv[2] === 'create') {
  const response = await fetch(`${APP_URL}/api/notes`, { method: 'POST', headers, body: JSON.stringify({ id: NOTE_ID, body: 'Saved before restart' }) });
  assert.equal(response.status, 201);
  assert.equal((await fetch(`${APP_URL}/api/notes`, { method: 'POST', headers, body: JSON.stringify({ id: NOTE_ID, body: 'Must not overwrite' }) })).status, 409);
  assert.equal((await fetch(`${APP_URL}/api/notes`, { method: 'POST', headers, body: '{}' })).status, 400);
}
const response = await fetch(`${APP_URL}/api/notes`, { headers });
assert.equal(response.status, 200);
assert.equal((await response.json()).notes.find(n => n.id === NOTE_ID)?.body, 'Saved before restart');
console.log('Health, auth, 404 and stored note checks passed');
