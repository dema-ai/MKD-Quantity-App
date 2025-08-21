import re
from pathlib import Path
import sys
from typing import List

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"

def local_modules() -> List[str]:
    return sorted([
        f.stem for f in APP.glob("*.py")
        if f.name not in {"__init__.py"}
    ])

def fix_file(path: Path, locals_: List[str]) -> int:
    text = path.read_text(encoding="utf-8")
    original = text

    # Normalize any malformed assumptions import variants
    text = re.sub(
        r"from\s+[A-Za-z0-9_\.]*assumptions\s+import\s+generate_assumptions",
        "from .assumptions import generate_assumptions",
        text,
    )

    # from module import X  -> from .module import X  (for local modules)
    for m in locals_:
        text = re.sub(
            rf"(?m)^(from)\s+{re.escape(m)}\s+(import)\s+",
            r"\1 ."+m+r" \2 ",
            text,
        )

    # import module  -> from . import module  (for local modules)
    # Handles comma lists: import a, b, c  (only rewrites single-local cases safely)
    def repl_import(match):
        mods = [s.strip() for s in match.group("mods").split(",")]
        if len(mods) == 1 and mods[0] in locals_:
            return f"from . import {mods[0]}"
        return match.group(0)

    text = re.sub(
        r"(?m)^(import)\s+(?P<mods>[A-Za-z0-9_ ,]+)$",
        repl_import,
        text,
    )

    if text != original:
        # Backup once
        bak = path.with_suffix(path.suffix + ".bak")
        if not bak.exists():
            bak.write_text(original, encoding="utf-8")
        path.write_text(text, encoding="utf-8")
        return 1
    return 0

def main():
    if not APP.exists():
        print(f"ERROR: {APP} not found")
        sys.exit(1)

    locals_ = local_modules()
    print("Local modules:", ", ".join(locals_) or "(none)")

    changed = 0
    for py in sorted(APP.glob("*.py")):
        if py.name == "__init__.py":
            continue
        changed += fix_file(py, locals_)
    print(f"Files changed: {changed}")

if __name__ == "__main__":
    main()
