"""Server operatsiyalari: status, restart, loglar."""
import os
import sys
import time

import paramiko

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HOST = os.environ.get("DEPLOY_HOST", "164.90.186.193")
USER = os.environ.get("DEPLOY_USER", "root")
PASSWORD = os.environ.get("DEPLOY_PASSWORD", "")
APP_DIR = "/opt/tgelon"
ACTION = os.environ.get("SERVER_ACTION", "status")


def run(ssh, cmd, timeout=120):
    print(f"$ {cmd}")
    _, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    code = stdout.channel.recv_exit_status()
    if out.strip():
        print(out.rstrip())
    if err.strip() and code != 0:
        print("ERR:", err.rstrip())
    return code, out


def main():
    if not PASSWORD:
        sys.exit("DEPLOY_PASSWORD kerak")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username=USER, password=PASSWORD, timeout=30)

    if ACTION == "status":
        run(ssh, "docker ps -a --filter name=tgelon --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}'")
        run(ssh, f"cd {APP_DIR} && docker compose -p tgelon ps")
        run(ssh, f"cd {APP_DIR} && docker compose -p tgelon logs --tail=30 2>&1")
    elif ACTION == "restart":
        run(ssh, f"cd {APP_DIR} && git pull origin main")
        run(ssh, f"cd {APP_DIR} && docker compose -p tgelon down")
        code, _ = run(ssh, f"cd {APP_DIR} && docker compose -p tgelon up -d --build --remove-orphans", timeout=600)
        time.sleep(5)
        run(ssh, f"cd {APP_DIR} && docker compose -p tgelon logs --tail=20 2>&1")
        run(ssh, "docker ps --filter name=tgelon-bot --format '{{.Names}} {{.Status}}'")
        return code
    elif ACTION == "health":
        run(ssh, f"cd {APP_DIR} && docker compose -p tgelon exec -T taxi-bot python scripts/health_check.py 2>&1")
    else:
        print(f"Noma'lum action: {ACTION}")
        return 1
    ssh.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
