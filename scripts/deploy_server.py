"""Serverga izolyatsiya qilingan Docker deploy (nginx ga tegmaydi)."""
import os
import sys
import time

import paramiko

HOST = os.environ.get("DEPLOY_HOST", "164.90.186.193")
USER = os.environ.get("DEPLOY_USER", "root")
PASSWORD = os.environ.get("DEPLOY_PASSWORD", "")
APP_DIR = "/opt/tgelon"
REPO = "https://github.com/aiziyrak-coder/tgelon.git"


def run(ssh: paramiko.SSHClient, cmd: str, timeout: int = 600) -> tuple[int, str, str]:
    print(f"$ {cmd}")
    _, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    code = stdout.channel.recv_exit_status()
    if out.strip():
        print(out.rstrip())
    if err.strip() and code != 0:
        print(err.rstrip(), file=sys.stderr)
    return code, out, err


def main() -> int:
    if not PASSWORD:
        print("DEPLOY_PASSWORD kerak", file=sys.stderr)
        return 1

    env_content = os.environ.get("DEPLOY_ENV_FILE", "")
    if not env_content:
        print("DEPLOY_ENV_FILE kerak", file=sys.stderr)
        return 1

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print(f"Ulanish: {USER}@{HOST}")
    ssh.connect(HOST, username=USER, password=PASSWORD, timeout=30)

    run(ssh, "docker --version")
    run(ssh, "docker compose version || docker-compose --version")

    # Faqat /opt/tgelon — boshqa loyihalarga tegmaymiz
    run(ssh, f"mkdir -p {APP_DIR}")
    code, out, _ = run(ssh, f"test -d {APP_DIR}/.git && echo yes || echo no")
    if "yes" in out:
        run(ssh, f"cd {APP_DIR} && git fetch origin && git reset --hard origin/main")
    else:
        run(ssh, f"rm -rf {APP_DIR}/* {APP_DIR}/.[!.]* 2>/dev/null; true")
        run(ssh, f"git clone {REPO} {APP_DIR}")

    sftp = ssh.open_sftp()
    with sftp.file(f"{APP_DIR}/.env", "w") as f:
        f.write(env_content)
    sftp.close()

    run(ssh, f"mkdir -p {APP_DIR}/data {APP_DIR}/logs")
    run(ssh, f"cd {APP_DIR} && docker compose -p tgelon down 2>/dev/null; true")
    code, _, _ = run(
        ssh,
        f"cd {APP_DIR} && docker compose -p tgelon up -d --build --remove-orphans",
        timeout=900,
    )
    if code != 0:
        return code

    time.sleep(4)
    run(ssh, "docker ps --filter name=tgelon-bot --format '{{.Names}} {{.Status}}'")
    run(ssh, f"cd {APP_DIR} && docker compose -p tgelon logs --tail=15")

    ssh.close()
    print("Deploy tugadi.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
