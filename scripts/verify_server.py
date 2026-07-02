import os
import sys

import paramiko

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

pwd = os.environ.get("DEPLOY_PASSWORD", "")
if not pwd:
    sys.exit("DEPLOY_PASSWORD kerak")

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("164.90.186.193", username="root", password=pwd, timeout=30)
_, o, _ = c.exec_command("docker ps --format '{{.Names}} | {{.Status}}'")
print(o.read().decode())
c.close()
