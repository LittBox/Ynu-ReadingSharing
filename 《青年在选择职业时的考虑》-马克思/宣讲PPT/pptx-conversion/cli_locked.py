"""Serialize public CLI state commands across page workers; no state logic."""
import fcntl,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parent
with (root/'run'/'.cli.lock').open('a') as lock:
    fcntl.flock(lock,fcntl.LOCK_EX)
    result=subprocess.run([sys.executable,str(root/'.image2ppt-runtime/cli/image2ppt/cli.py'),*sys.argv[1:]])
sys.exit(result.returncode)
