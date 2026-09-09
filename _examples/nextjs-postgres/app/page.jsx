export default function Page() {
  return <main><h1>Notes with Managed Postgres</h1><p>This example stores notes in Postgres. The API requires a bearer token.</p><p>Use the guide's check script to create a note, restart the service, and read the same note.</p><p><a href="/health">Check database readiness</a></p></main>;
}
