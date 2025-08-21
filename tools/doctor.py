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
