#!/usr/bin/env python3

import getpass
import shutil as sh
import subprocess as sp
import sys
import os
import time

# This script is executed on codegrade during the initial shared setup.

grade_dir = os.path.dirname(os.path.realpath(__file__))
base_dir = os.path.realpath(os.path.join(grade_dir, "..", ".."))

if getpass.getuser() != "codegrade":
    print("This is supposed to run on the codegrade environment. Exiting...")
    sys.exit(1)

os.chdir(base_dir)
# If we're in a git repo, clean it from build files.
sp.run(["git", "clean", "-fdx"], cwd=base_dir, stderr=sp.DEVNULL, stdout=sp.DEVNULL)
# Get rid of the git folder to save snapshot space.
sh.rmtree(os.path.join(base_dir, ".git"), ignore_errors=True)

# Setup docker.
sp.run(["sudo", "groupadd", "docker"], check=False)
sp.run(["sudo", "usermod", "-aG", "docker", "codegrade"], check=False)

sp.check_call(["bash", "-lc", "curl -fsSL https://get.docker.com -o install-docker.sh"])
sp.check_call(["sudo", "sh", "install-docker.sh"])
os.remove("install-docker.sh")

# --- CodeGrade runner fix ---
# Docker fails to start here due to nftables/iptables restrictions:
# "failed to create NAT chain DOCKER ... nf_tables ... Invalid argument"
daemon_json = r'''{
  "iptables": false,
  "bridge": "none",
  "ip-forward": false,
  "ip-masq": false,
  "features": { "buildkit": false }
}
'''
sp.check_call(["sudo", "mkdir", "-p", "/etc/docker"])
sp.check_call(["bash", "-lc", f"cat > /tmp/daemon.json <<'EOF'\n{daemon_json}\nEOF"])
sp.check_call(["sudo", "mv", "/tmp/daemon.json", "/etc/docker/daemon.json"])

# Restart docker and wait until it is actually ready.
sp.run(["sudo", "systemctl", "reset-failed", "docker.service"], check=False)
sp.run(["sudo", "systemctl", "restart", "docker.service"], check=False)

ok = False
for _ in range(30):
    if sp.run(["sudo", "docker", "info"], stdout=sp.DEVNULL, stderr=sp.DEVNULL).returncode == 0:
        ok = True
        break
    time.sleep(1)

if not ok:
    # Dump logs to make debugging obvious in CodeGrade output.
    sp.run(["sudo", "systemctl", "status", "docker.service", "--no-pager", "-l"], check=False)
    sp.run(["sudo", "journalctl", "-u", "docker.service", "--no-pager", "-n", "200"], check=False)
    sys.exit(1)

# Build the container for the first time so the image is cached.
run_py = os.path.join(base_dir, "run.py")

env = os.environ.copy()
env["DOCKER_BUILDKIT"] = "0"   # belt-and-suspenders

sp.check_call([run_py, "-l", "-c", "ls"], env=env)
