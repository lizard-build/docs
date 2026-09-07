import { execFileSync } from 'node:child_process';
import { setTimeout } from 'node:timers/promises';

const service = process.argv[2];
const url = process.env.APP_URL;
if (!service || !url) throw new Error('Set APP_URL and pass the service name');

async function health() {
  const response = await fetch(`${url}/health`, { signal: AbortSignal.timeout(5000), cache: 'no-store' });
  if (!response.ok) throw new Error(`Health returned ${response.status}`);
  const body = await response.json();
  if (body.ready !== true || typeof body.instanceId !== 'string' || !body.instanceId) {
    throw new Error('Health must include ready and instanceId');
  }
  return body.instanceId;
}

const before = await health();
execFileSync('lizard', ['restart', '--service', service, '--json'], { stdio: 'inherit', timeout: 30000 });
const deadline = Date.now() + 120000;
let candidate;
let stable = 0;
while (Date.now() < deadline) {
  try {
    const current = await health();
    stable = current !== before ? (current === candidate ? stable + 1 : 1) : 0;
    candidate = current;
    if (stable >= 3) {
      console.log(`Replacement process ready: ${before} -> ${current}`);
      process.exit(0);
    }
  } catch { stable = 0; }
  await setTimeout(2000);
}
throw new Error('No stable replacement process within 120 seconds; inspect lizard events and logs');
