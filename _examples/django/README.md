# Django deployment example

This example accompanies the [Django guide for Lizard (lizard.build)](https://lizard.build/docs/framework-guides/django/). It uses PostgreSQL, Gunicorn, and WhiteNoise. The home page saves short notes through a CSRF-protected form; Django admin supplies the static assets used by the checks.

The form is a test fixture with no sign-in or rate limit. Use it to check deployment steps, not as a public notes service.

## Run the checks locally

Requirements: Python 3 on the host and a running Docker engine. Copy this directory into a standalone local folder, then run:

```bash
python3 tests/verify.py --report /tmp/django-example-checks.json
```

The runner builds the Dockerfile, installs the versions in `requirements.txt`, and starts PostgreSQL 18 and Gunicorn on a private Docker network. Only the app gets a host port, bound to `127.0.0.1`. It generates temporary credentials and does not call Lizard or change any cloud service.

The checks cover:

- Image build and `collectstatic` with no reachable database, including a separate run with networking disabled.
- Absence of build placeholders from the image's runtime environment.
- Gunicorn startup failure without required settings; rejection of absent, empty, and whitespace values.
- Explicit parsing of `DEBUG=false` and rejection of invalid boolean values.
- PostgreSQL migrations, a second migration run, and agreement between models and migrations.
- An HTTP form write, ORM read, and persistence after database and app restarts.
- CSRF rejection without a token or with an untrusted origin, plus acceptance of an explicitly trusted origin.
- Rejection of an unknown host, missing routes, admin CSS through WhiteNoise, and missing static assets.

The runner also records `check --deploy` output. HTTPS redirects, secure cookies, and HSTS need a real proxy and domain before their settings can be verified. Local HTTP checks do not verify the Lizard proxy, a cloud deployment, backups, uploaded files, or multiple replicas.

The runner stops all containers it creates, including on failure. It retains stopped containers, the PostgreSQL volume, the Docker network, and the image for inspection. Their names appear in the report; review them before removing anything. The report contains no generated credentials.

### September 14, 2026 result

All 12 check groups passed in local Linux containers: Python 3.13.15, Django 6.1.1, Gunicorn 26.2.0, WhiteNoise 6.12.0, psycopg 3.3.5, dj-database-url 3.1.2, and PostgreSQL 18.6. `check --deploy` reported four warnings for HSTS, HTTPS redirects, and secure session and CSRF cookies. The test uses local HTTP and does not silence those warnings. This revised example has not had a new cloud deployment.

## Configure an existing Django app

Use the environment-reading block from `config/settings.py` in your own settings. Keep your app's other settings; remove older assignments that would overwrite the new values. Include all five direct dependencies in `requirements.txt` and preserve your app's other dependencies. The file pins the tested direct package versions, not every transitive dependency or container image digest.

Required runtime values:

| Variable | Value |
|---|---|
| `SECRET_KEY` | A fresh random secret |
| `DATABASE_URL` | The PostgreSQL URL for this app |
| `ALLOWED_HOSTS` | Comma-separated hostnames, without schemes or paths |
| `CSRF_TRUSTED_ORIGINS` | Comma-separated origins, including `https://` for the public app |
| `DEBUG` | `false` on the deployed service; defaults to `false` |

The Dockerfile supplies placeholders only for asset collection. Those values do not persist as runtime environment variables. Do not query the database during settings imports or `AppConfig.ready()`.

## Deploy a local copy

Follow the [full Django guide](https://lizard.build/docs/framework-guides/django/#deploy-and-verify) to create the app service, add Managed Postgres, set service secrets and the database reference, and upload this directory with port `8000`. Set the public hostname and HTTPS origin, then run migrations as a separate step. Use `.gitignore` for source-upload exclusions and `.dockerignore` for Docker context exclusions.

For a GitHub deployment, put this example at the root of your own repository and follow the [GitHub guide](https://lizard.build/docs/deploy/github/). Do not run `lizard up` on a service that should keep its GitHub source.
