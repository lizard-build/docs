import { generateKeyPair, exportSPKI, SignJWT } from 'jose';
import { writeFile } from 'node:fs/promises';
const { publicKey, privateKey } = await generateKeyPair('RS256', { extractable: true });
const token = await new SignJWT({}).setProtectedHeader({ alg: 'RS256' })
  .setIssuer('mcp-example').setAudience('mcp-example').setExpirationTime('1h').sign(privateKey);
await writeFile('.mcp-public-key.pem', await exportSPKI(publicKey), { mode: 0o600, flag: 'wx' });
await writeFile('.mcp-token', token, { mode: 0o600, flag: 'wx' });
console.log('Wrote a test public key and a one-hour client token. The private key was not saved.');
