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
