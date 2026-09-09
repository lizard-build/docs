export const metadata = { title: 'Notes with Managed Postgres', robots: { index: false, follow: false } };
export default function Layout({ children }) {
  return <html lang="en"><body style={{ fontFamily: 'system-ui', maxWidth: 720, margin: '4rem auto', padding: '0 24px' }}>{children}</body></html>;
}
