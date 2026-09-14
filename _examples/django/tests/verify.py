"""Exercise the documented Docker image over HTTP and real PostgreSQL."""
import argparse
import http.cookiejar
import json
from pathlib import Path
import re
import secrets
import subprocess
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
checks = []
containers = []


def run(*args, check=True):
    result = subprocess.run(args, cwd=ROOT, text=True, capture_output=True)
    if check and result.returncode:
        raise RuntimeError(f"Command failed: {args[0]} {args[1]}\n{result.stdout}\n{result.stderr}")
    return result


def passed(name):
    checks.append(name)
    print(f"PASS {name}", flush=True)


def wait_for(check, label):
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        try:
            if check():
                return
        except (OSError, urllib.error.URLError):
            pass
        time.sleep(0.5)
    raise RuntimeError(f"Timed out waiting for {label}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", default="lizard-django-guide:test")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    suffix = secrets.token_hex(4)
    network = f"django-guide-{suffix}"
    db, app = f"{network}-db", f"{network}-app"
    result = {"checks": checks, "network": network, "containers": containers}
    try:
        run("docker", "build", "-t", args.image, ".")
        passed("Docker image builds and collects static assets")
        result["image"] = run("docker", "image", "inspect", args.image, "--format", "{{.Id}}").stdout.strip()
        image_env = run("docker", "image", "inspect", args.image, "--format", "{{json .Config.Env}}").stdout
        assert not any(f"{name}=" in image_env for name in ["SECRET_KEY", "DATABASE_URL", "ALLOWED_HOSTS", "CSRF_TRUSTED_ORIGINS"])
        passed("Build placeholders are absent from the image environment")
        run("docker", "network", "create", network)
        with tempfile.TemporaryDirectory(prefix="django-guide-") as temp:
            temp = Path(temp)
            db_password = secrets.token_urlsafe(24)
            environment = {
                "SECRET_KEY": secrets.token_urlsafe(64),
                "DATABASE_URL": f"postgresql://example:{db_password}@{db}:5432/example",
                "DEBUG": "false",
                "ALLOWED_HOSTS": "localhost, 127.0.0.1",
                "CSRF_TRUSTED_ORIGINS": "http://localhost, https://forms.example.test",
            }
            app_env, db_env = temp / "app.env", temp / "db.env"
            for path, values in [(app_env, environment), (db_env, {
                "POSTGRES_USER": "example", "POSTGRES_DB": "example", "POSTGRES_PASSWORD": db_password,
            })]:
                path.write_text("".join(f"{key}={value}\n" for key, value in values.items()))
                path.chmod(0o600)

            offline = f"{network}-offline"
            containers.append(offline)
            run("docker", "run", "--name", offline, "--network", "none", "--env-file", str(app_env),
                args.image, "python", "manage.py", "collectstatic", "--noinput")
            passed("collectstatic runs with networking disabled and no reachable database")

            no_env = f"{network}-missing-env"
            containers.append(no_env)
            failed = run("docker", "run", "--name", no_env, "--network", "none", args.image, check=False)
            assert failed.returncode != 0 and "Set the SECRET_KEY environment variable." in failed.stderr
            passed("Default Gunicorn startup fails without runtime secrets")

            containers.append(db)
            run("docker", "run", "-d", "--name", db, "--network", network,
                "--env-file", str(db_env), "postgres:18")
            ready = lambda: run("docker", "exec", db, "pg_isready", "-U", "example", "-d", "example", check=False).returncode == 0
            wait_for(ready, "PostgreSQL")
            containers.append(app)
            run("docker", "run", "-d", "--name", app, "--network", network,
                "--env-file", str(app_env), "-p", "127.0.0.1::8000", args.image)
            port = run("docker", "port", app, "8000/tcp").stdout.strip().rsplit(":", 1)[1]
            base = f"http://127.0.0.1:{port}"
            result["url"] = base

            for name in ["SECRET_KEY", "DATABASE_URL", "ALLOWED_HOSTS", "CSRF_TRUSTED_ORIGINS"]:
                for value_args in [("-u", name), (f"{name}=",), (f"{name}=   ",)]:
                    failed = run("docker", "exec", app, "env", *value_args, "python", "manage.py", "check", check=False)
                    assert failed.returncode != 0 and f"Set the {name} environment variable." in failed.stderr
            passed("Each required variable rejects absent, empty, and whitespace values")
            failed = run("docker", "exec", app, "env", "DEBUG=not-a-boolean", "python", "manage.py", "check", check=False)
            assert failed.returncode != 0 and "DEBUG must be true or false." in failed.stderr
            false_value = run("docker", "exec", app, "python", "manage.py", "shell", "-c", "from django.conf import settings; assert settings.DEBUG is False").returncode
            assert false_value == 0
            passed("DEBUG=false is false; invalid boolean values fail")

            run("docker", "exec", app, "python", "manage.py", "migrate", "--noinput")
            second = run("docker", "exec", app, "python", "manage.py", "migrate", "--noinput")
            assert "No migrations to apply" in second.stdout
            run("docker", "exec", app, "python", "manage.py", "makemigrations", "--check", "--dry-run")
            passed("PostgreSQL migrations apply once and a second run has no pending migrations")
            deployment = run("docker", "exec", app, "python", "manage.py", "check", "--deploy")
            result["deployment_check"] = deployment.stdout + deployment.stderr

            cookies = http.cookiejar.CookieJar()
            opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookies))

            def request(path="/", data=None, headers=None):
                req = urllib.request.Request(base + path, data=urllib.parse.urlencode(data).encode() if data is not None else None, headers=headers or {})
                try:
                    response = opener.open(req, timeout=5)
                except urllib.error.HTTPError as error:
                    response = error
                with response:
                    return response.status, response.read().decode(), response.headers

            wait_for(lambda: request()[0] == 200, "Gunicorn HTTP")
            status, body, _ = request()
            assert status == 200 and "Django deployment example" in body
            token = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', body)[1]
            note = "verified-" + suffix
            assert request(data={"text": note, "csrfmiddlewaretoken": token})[0] == 200
            assert note in request()[1]
            run("docker", "exec", app, "python", "manage.py", "shell", "-c",
                f"from notes.models import Note; assert Note.objects.get(text='{note}').text == '{note}'")
            passed("Gunicorn serves the page and a CSRF form writes and reads a PostgreSQL row")
            assert request(data={"text": "rejected"})[0] == 403
            assert request(data={"text": "rejected", "csrfmiddlewaretoken": token}, headers={"Origin": "https://untrusted.example.test"})[0] == 403
            assert request(data={"text": "trusted-origin", "csrfmiddlewaretoken": token}, headers={"Origin": "https://forms.example.test"})[0] == 200
            run("docker", "exec", app, "python", "manage.py", "shell", "-c", "from notes.models import Note; assert Note.objects.count() == 2")
            passed("CSRF rejects missing tokens and untrusted origins; explicit trusted origin succeeds")
            assert request(headers={"Host": "untrusted.example.test"})[0] == 400
            assert request("/missing-page/")[0] == 404
            passed("Unknown hosts return 400 and missing routes return 404")

            status, body, _ = request("/admin/login/")
            assert status == 200
            styles = re.findall(r'href="(/static/[^"?]+\.css)"', body)
            assert styles
            for path in styles:
                status, css, headers = request(path)
                assert status == 200 and len(css) > 100 and "text/css" in headers["Content-Type"]
            assert request("/static/missing.css")[0] == 404
            passed(f"WhiteNoise serves all {len(styles)} admin CSS files with DEBUG=false")
            run("docker", "restart", db)
            wait_for(ready, "PostgreSQL restart")
            run("docker", "restart", app)
            port = run("docker", "port", app, "8000/tcp").stdout.strip().rsplit(":", 1)[1]
            base = f"http://127.0.0.1:{port}"
            result["url_after_restart"] = base
            wait_for(lambda: request()[0] == 200, "Gunicorn restart")
            assert note in request()[1]
            passed("Database row survives PostgreSQL and Gunicorn restarts")
            result["versions"] = run("docker", "exec", app, "python", "-c",
                "import sys,importlib.metadata as m,json; print(json.dumps({'python':sys.version,**{n:m.version(n) for n in ['Django','gunicorn','whitenoise','psycopg','dj-database-url']}}))").stdout.strip()
            result["postgres"] = run("docker", "exec", db, "postgres", "--version").stdout.strip()
        result["passed"] = True
    finally:
        for container in reversed(containers):
            run("docker", "stop", container, check=False)
        result["retained_resources"] = "Test containers are stopped. Containers, network, image, and PostgreSQL volume are retained."
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
