# Next.js with Managed Postgres

Runnable source for the [Next.js and Postgres guide](https://lizard.build/docs/guides/nextjs-postgres/).

Use Node.js 22 and `npm ci`. `npm run build` needs no database. At runtime set `DATABASE_URL` and a random `API_TOKEN` of at least 32 characters. `npm start` runs transactional SQL migrations before starting Next.js on port 3000.

Run `node --env-file=.env scripts/check.mjs create` with `APP_URL` and a UUID v4 `NOTE_ID` exported. Restart the service, then run the same command with `read`. Keep the same note ID. The read check never seeds data.

The demo has one shared API token, one replica and a five-connection pool. It stores no private user data, has no user account system and does not test database backups. Keep applied migrations unchanged; add a new numbered SQL file for later changes.
