import 'server-only';
import { timingSafeEqual } from 'node:crypto';
export function authorized(request) {
  const token = process.env.API_TOKEN;
  if (!token || token.length < 32) return false;
  const actual = Buffer.from(request.headers.get('authorization') ?? '');
  const expected = Buffer.from(`Bearer ${token}`);
  return actual.length === expected.length && timingSafeEqual(actual, expected);
}
