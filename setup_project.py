import os
from pathlib import Path

BASE = Path.cwd()
folders = [
    "tools",
    "mkd/utils",
    "mkd/reporting",
    "bin",
    "templates",
    "inputs",
    "outputs",
    "logs"
]

files = {
    "app.py": """\
import os
import pandas as pd
from mkd.utils.reliability import retry
from mkd.reporting.exporters import export_boq

@retry()
def build_dataframe():
    return pd.DataFrame([{"Item": "Concrete", "Qty": 25}, {"Item": "Steel", "Qty": 10}])

def main():
    df = build_dataframe()
    base = os.path.join("outputs", "BoQ_Demo")
    out = export_boq(df, base)
    print(f"✅ Output written: {out}")

if __name__ == "__main__":
    main()
""",

    "requirements.lock.txt": """\
pandas==2.2.2
openpyxl==3.1.2
jinja2==3.1.4
""",

    "tools/doctor.py": """\
import sys, os

REQUIRED = {
    "python_min": (3, 10),
    "packages": {
        "pandas": "2.2.2",
        "openpyxl": "3.1.2",
        "jinja2": "3.1.4"
    },
    "binaries": {
        "wkhtmltopdf": "bin/wkhtmltopdf.exe"
    },
    "paths": ["outputs", "inputs", "templates", "logs"]
}

def fail(msg): print(f"[FAIL] {msg}"); sys.exit(1)
def ok(msg): print(f"[OK] {msg}")

def check_python():
    if sys.version_info < REQUIRED["python_min"]:
        fail("Python version too low")
    ok("Python version OK")

def check_packages():
    for pkg, ver in REQUIRED["packages"].items():
        try:
            mod = __import__(pkg)
            if mod.__version__ != ver:
                fail(f"{pkg} version mismatch")
            ok(f"{pkg}=={ver}")
        except Exception:
            fail(f"{pkg} not installed")

def check_binaries():
    for name, path in REQUIRED["binaries"].items():
        if not os.path.isfile(path):
            fail(f"{name} missing at {path}")
        ok(f"{name} found")

def check_paths():
    for p in REQUIRED["paths"]:
        os.makedirs(p, exist_ok=True)
        test = os.path.join(p, "test.tmp")
        try:
            with open(test, "w") as f: f.write("ok")
            os.remove(test)
            ok(f"{p} writable")
        except Exception:
            fail(f"{p} not writable")

def main():
    print("[DOCTOR] Running preflight checks…")
    check_python()
    check_packages()
    check_binaries()
    check_paths()
    print("[DOCTOR] All checks passed.")

if __name__ == "__main__":
    main()
""",

    "mkd/utils/reliability.py": """\
import time, functools, random

def retry(max_attempts=3, base=0.5, jitter=0.2, exceptions=(Exception,)):
    def deco(fn):
        @functools.wraps(fn)
        def wrap(*a, **k):
            for attempt in range(max_attempts):
                try:
                    return fn(*a, **k)
                except exceptions:
                    if attempt == max_attempts - 1:
                        raise
                    time.sleep(base * (2 ** attempt) + random.uniform(0, jitter))
        return wrap
    return deco
""",

    "mkd/utils/io.py": """\
import os, tempfile, hashlib, json, time

def atomic_write(path, data_bytes):
    d = os.path.dirname(path)
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".tmp_", dir=d)
    with os.fdopen(fd, "wb") as f:
        f.write(data_bytes)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)

def write_manifest(final_path, extras):
    h = hashlib.sha256(open(final_path, "rb").read()).hexdigest()
    manifest = {
        "file": os.path.basename(final_path),
        "sha256": h,
        "created": int(time.time()),
        **extras
    }
    with open(final_path + ".manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
""",

    "mkd/reporting/exporters.py": """\
import pandas as pd

def export_boq(df, path_base):
    try:
        with pd.ExcelWriter(f"{path_base}.xlsx", engine="openpyxl") as w:
            df.to_excel(w, index=False)
        return f"{path_base}.xlsx"
    except Exception:
        df.to_csv(f"{path_base}.csv", index=False, encoding="utf-8-sig")
        df.to_html(f"{path_base}.html", index=False)
        return f"{path_base}.csv"
""",

    "launch.ps1": """\
$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $here

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$logDir = Join-Path $here "logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
Start-Transcript -Path (Join-Path $logDir "run_$stamp.log") | Out-Null

$venv = Join-Path $here "venv\\Scripts\\Activate.ps1"
. $venv

function Fail-Friendly($msg) {
  Write-Host "`n=== DEMO-SAFE ERROR ===" -ForegroundColor Red
  Write-Host $msg -ForegroundColor Yellow
  Write-Host "A support bundle was created in the logs/ folder." -ForegroundColor Yellow
  Stop-Transcript | Out-Null
  exit 1
}

try {
  python tools/doctor.py
} catch {
  Compress-Archive -Path $logDir\\* -DestinationPath (Join-Path $logDir "support_$stamp.zip") -Force
  Fail-Friendly "Preflight failed. Fix the issues and re-run."
}

try {
  python app.py
} catch {
  Compress-Archive -Path $logDir\\* -DestinationPath (Join-Path $logDir "support_$stamp.zip") -Force
  Fail-Friendly "App execution failed. Check logs for details."
}

Stop-Transcript | Out-Null
Write-Host "`n✅ Run completed successfully." -ForegroundColor Green
exit 0
"""
}

# Create folders
for folder in folders:
    Path(BASE / folder).mkdir(parents=True, exist_ok=True)

# Create files
for path, content in files.items():
    full_path = BASE / path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content.strip() + "\n", encoding="utf-8")

print("✅ Project structure generated successfully.")