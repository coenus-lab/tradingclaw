"""Disposable integration check. Requires Docker Compose v2 with --wait support."""
import base64
import json
import os
from pathlib import Path
import secrets
import subprocess
import tempfile
import time
import urllib.error
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
VARIABLES = ("POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD", "JWT_SECRET", "ENCRYPTION_KEY")


def main():
    # Never reuse operator secrets, project names, or volumes.
    env = {k: v for k, v in os.environ.items()
           if k not in VARIABLES and not k.startswith("COMPOSE_")}
    project = "tradingclaw-smoke-" + secrets.token_hex(6)
    values = dict(zip(VARIABLES, ("smoke", "smoke_user", secrets.token_hex(32),
                                 secrets.token_hex(32), base64.urlsafe_b64encode(os.urandom(32)).decode())))
    with tempfile.TemporaryDirectory(prefix="tradingclaw-smoke-") as folder:
        envfile = Path(folder) / "smoke.env"
        envfile.touch(mode=0o600)

        def write_env(data):
            envfile.write_text("".join(f"{k}={v}\n" for k, v in data.items()))

        def compose(*args, check=True):
            return subprocess.run(
                ["docker", "compose", "--project-name", project, "--env-file", str(envfile),
                 "-f", str(ROOT / "docker-compose.yml"), *args],
                cwd=ROOT, env=env, text=True, capture_output=True, check=check,
            )

        write_env(values)
        compose("config", "--quiet")
        for variable in VARIABLES:
            for empty in (False, True):
                invalid = values.copy()
                invalid[variable] = ""
                if not empty:
                    del invalid[variable]
                write_env(invalid)
                result = compose("config", "--quiet", check=False)
                assert result.returncode != 0 and variable in result.stderr, variable
        write_env(values)
        print("PASS: valid interpolation; each missing/empty variable rejected", flush=True)

        try:
            compose("up", "--build", "--detach", "--wait", "--wait-timeout", "180")
            services = set(compose("ps", "--services", "--status", "running").stdout.split())
            assert services == {"db", "redis", "backend", "frontend"}, services
            compose("exec", "-T", "db", "pg_isready", "-h", "127.0.0.1", "-U", values["POSTGRES_USER"], "-d", values["POSTGRES_DB"])
            assert compose("exec", "-T", "redis", "redis-cli", "ping").stdout.strip() == "PONG"

            # Resolve published ports rather than assuming a host interface.
            def base_url(service, port):
                address = compose("port", service, str(port)).stdout.strip().splitlines()[0]
                return "http://127.0.0.1:" + address.rsplit(":", 1)[1]

            api = base_url("backend", 8000)
            frontend = base_url("frontend", 3000)

            def request(path, payload=None, token=None):
                headers = {"Content-Type": "application/json"}
                if token:
                    headers["Authorization"] = "Bearer " + token
                data = json.dumps(payload).encode() if payload is not None else None
                with urllib.request.urlopen(urllib.request.Request(api + path, data, headers), timeout=5) as response:
                    return json.load(response)

            assert request("/health") == {"status": "ok"}
            with urllib.request.urlopen(frontend, timeout=10) as response:
                assert response.status == 200
            credentials = {"email": "smoke@example.test", "password": secrets.token_hex(24)}
            user_id = request("/v1/auth/register", credentials)["id"]
            login = request("/v1/auth/login", credentials)
            assert login["user_id"] == user_id and login["role"] == "trader"
            token = login["token"]
            assert request(f"/v1/users/{user_id}/events", token=token) == []
            try:
                request(f"/v1/users/{user_id}/events")
                raise AssertionError("Anonymous sensitive request was accepted")
            except urllib.error.HTTPError as exc:
                assert exc.code == 401
            dummy = "smoke-secret-" + secrets.token_hex(16)
            assert request("/v1/credentials", {"environment": "demo", "api_key": "dummy", "api_secret": dummy}, token)["ok"]
            print("PASS: four services ready; HTTP, login, authorization and credential storage", flush=True)

            compose("restart", "backend")
            deadline = time.monotonic() + 60
            while True:
                try:
                    assert request("/health") == {"status": "ok"}
                    break
                except (OSError, AssertionError):
                    if time.monotonic() >= deadline:
                        raise
                    time.sleep(1)
            # A fresh container process reads the database ciphertext using the same key.
            code = (
                "from app.core.db import SessionLocal; "
                "from app.core.security import decrypt_secret; "
                "from app.models.entities import ApiCredential; "
                "import sys; "
                "db=SessionLocal(); row=db.query(ApiCredential).one(); "
                "expected=sys.stdin.read(); "
                "assert row.api_secret_encrypted != expected; "
                "assert decrypt_secret(row.api_secret_encrypted) == expected; db.close()"
            )
            command = ["docker", "compose", "--project-name", project, "--env-file", str(envfile),
                       "-f", str(ROOT / "docker-compose.yml"), "exec", "-T", "backend", "python", "-c", code]
            subprocess.run(command, input=dummy, env=env, cwd=ROOT, text=True,
                           capture_output=True, check=True)
            request(f"/v1/users/{user_id}/events", token=token)
            print("PASS: persisted ciphertext decrypts after backend restart; JWT remains usable", flush=True)
        except Exception:
            diagnostics = compose("logs", "--no-color", "--tail", "80", check=False)
            output = diagnostics.stdout + diagnostics.stderr
            # Validation errors can include input values; never publish generated secrets.
            for value in (*values.values(), locals().get("dummy", ""), locals().get("token", "")):
                if value:
                    output = output.replace(value, "[redacted]")
            print(output, flush=True)
            raise
        finally:
            # Only this random project's containers and disposable volume are removed.
            result = compose("down", "--volumes", "--remove-orphans", check=False)
            if result.returncode:
                raise RuntimeError(f"Cleanup failed for disposable project {project}")


if __name__ == "__main__":
    main()
