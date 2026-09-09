# Flowise on Lizard (lizard.build)

This guide runs one Flowise service on Lizard, with PostgreSQL for flows, accounts, and encrypted credentials. It builds an exact npm version and sets the encryption key as a service secret.

The basic setup covers flows that use APIs. Uploaded files and local vector stores need separate persistent storage; see [File storage](#file-storage) before using those features.

## Prerequisites

- A Lizard account with access to app hosting and Managed Postgres.
- Node.js, npm, and OpenSSL on your computer.
- Enough memory for your Flowise workload; the test service uses 4 GiB.

Install Lizard CLI and finish the browser login:

```bash
npm install -g @lizard-build/cli
lizard login
```

## Create the project

```bash
mkdir flowise-on-lizard
cd flowise-on-lizard
lizard init --name flowise-on-lizard
lizard add postgres --name flowise-db
lizard add --service flowise
```

Use `--workspace <workspace>` with `lizard init` if you need to select a workspace. Wait until the database is running.

## Build a fixed Flowise version

Create `Dockerfile` with the contents below. This follows the Flowise Docker build and fixes the npm package at `3.1.4`:

```dockerfile
FROM node:24-alpine AS build
RUN apk add --no-cache git python3 py3-pip py3-setuptools make g++ build-base cairo-dev pango-dev
ENV PUPPETEER_SKIP_DOWNLOAD=true
RUN npm install -g flowise@3.1.4 --legacy-peer-deps

FROM node:24-alpine
RUN apk add --no-cache chromium git python3 py3-pip py3-setuptools make g++ build-base cairo-dev pango-dev curl
ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium-browser
COPY --from=build /usr/local/lib/node_modules /usr/local/lib/node_modules
COPY --from=build /usr/local/bin /usr/local/bin
RUN chown -R node:node /usr/local/lib/node_modules /usr/local/bin
USER node
EXPOSE 3000
ENTRYPOINT ["flowise", "start"]
```

`--legacy-peer-deps` avoids installing optional peer integrations, including an old native SQLite dependency. This recipe targets PostgreSQL and API-based flows; install and test extra dependencies separately for nodes that need them.

Select the Dockerfile explicitly:

```bash
lizard service set flowise --set dockerfilePath=Dockerfile
```

## Configure PostgreSQL and encryption

Reference the database variables on the Flowise service:

```bash
lizard secrets set \
  DATABASE_TYPE=postgres \
  DATABASE_HOST='${{flowise-db.PGHOST}}' \
  DATABASE_PORT='${{flowise-db.PGPORT}}' \
  DATABASE_USER='${{flowise-db.PGUSER}}' \
  DATABASE_PASSWORD='${{flowise-db.PGPASSWORD}}' \
  DATABASE_NAME='${{flowise-db.PGDATABASE}}' \
  --service flowise
```

Keep the single quotes so your shell does not expand the references. Lizard resolves them when the service starts.

Generate the following secrets once during setup:

```bash
lizard secrets set \
  FLOWISE_SECRETKEY_OVERWRITE="$(openssl rand -hex 32)" \
  JWT_AUTH_TOKEN_SECRET="$(openssl rand -hex 32)" \
  JWT_REFRESH_TOKEN_SECRET="$(openssl rand -hex 32)" \
  EXPRESS_SESSION_SECRET="$(openssl rand -hex 32)" \
  TOKEN_HASH_SECRET="$(openssl rand -hex 32)" \
  SECURE_COOKIES=true \
  --service flowise
```

Keep a secure copy of these values. In particular, preserve `FLOWISE_SECRETKEY_OVERWRITE`: Flowise needs the same key to decrypt credentials already stored in PostgreSQL. Do not regenerate the secrets when restarting, redeploying, or upgrading.

## Deploy and create your account

```bash
lizard up --service flowise --port 3000
```

The first build installs Flowise and its dependencies, so it can take several minutes. Open the HTTPS URL returned by the deployment and create the first owner account before sharing the URL. Sign in to the editor.

Set the public URL for links that Flowise generates, replacing the example with your actual HTTPS URL:

```bash
lizard secrets set APP_URL=https://YOUR-SERVICE.onlizard.com --service flowise
```

This change restarts the service. Configure SMTP separately if you need password-reset or invitation emails.

## Verify persistence

Create and save a flow. Add a test credential, then restart Flowise:

```bash
lizard restart --service flowise
```

Wait until the service is running, sign in again, and check that the flow and credential remain. Run a flow that uses the credential to confirm that Flowise can still decrypt it. Repeat the check after redeploying:

```bash
lizard redeploy --service flowise
```

Back up both PostgreSQL and the encryption key. A database backup without the key cannot recover saved credentials.

## File storage

PostgreSQL does not store every file that Flowise writes. This setup does not mount a persistent file volume, so local uploads, local vector databases, and file logs can disappear when the container is replaced.

Before using uploads or document workflows, configure a private S3 bucket using Flowise's [storage variables](https://docs.flowiseai.com/configuration/environment-variables). Set `STORAGE_TYPE=s3`, `S3_STORAGE_BUCKET_NAME`, `S3_STORAGE_ACCESS_KEY_ID`, `S3_STORAGE_SECRET_ACCESS_KEY`, and `S3_STORAGE_REGION`. For an S3-compatible provider, also set `S3_ENDPOINT_URL` and `S3_FORCE_PATH_STYLE=true`.

Lizard's Managed Object Storage creates a public-read `default` bucket. Do not put private Flowise documents in that bucket without first changing its access setting. The PostgreSQL setup above does not provision or test file storage, local vector stores, or queue workers.

## Troubleshooting and updates

```bash
lizard events --service flowise
lizard logs --build --service flowise
lizard logs --service flowise
```

If a first deployment times out while the image is still being pulled, inspect `lizard events`. Once the container has started, retry `lizard up --service flowise --port 3000`. A service with no successful prior build cannot use `lizard redeploy` yet.

For updates, back up the database, read Flowise's release notes, change the npm version in the Dockerfile, and upload it again with `lizard up`. Verify the new version and run the persistence checks before relying on the update.
