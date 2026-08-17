import subprocess, pathlib, sys

html = pathlib.Path(r"C:\Users\IT008\WorkBuddy\2026-08-13-task-21\website\index.html").read_text(encoding="utf-8")

cmd = [
    "npx.cmd", "-y", "--registry=https://registry.npmjs.org", "mcporter", "call",
    "mcp-on-edge.edgeone.app/mcp-server.deploy-html",
    "value=" + html,
]

result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)
sys.stdout.write(result.stdout)
if result.stderr:
    sys.stderr.write("\n[stderr]\n" + result.stderr)
