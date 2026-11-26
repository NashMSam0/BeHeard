"""Explicit public file boundary. Never reads the private directory or database."""
from io import BytesIO
import json
import os
from pathlib import Path
import zipfile

from public_views import render_public
from seo import add_metadata, robots_text, sitemap_xml
from public_manifest import PUBLIC_PAGES, PUBLIC_ASSETS, PUBLIC_FILES, MAX_ARTIFACT_BYTES, artifact_digest

def collect_public(app):
    public = Path(app.static_folder)
    origin = app.config["PUBLIC_ORIGIN"]
    files = {}
    with app.app_context():
        for name in PUBLIC_PAGES:
            if (public / name).is_symlink():
                raise ValueError("Public pages cannot be symlinks")
            path = "/" if name == "index.html" else "/" + name
            files[name] = add_metadata(render_public(public, name), path, origin).encode("utf-8")
    for name in PUBLIC_ASSETS:
        path = public / name
        if path.is_symlink():
            raise ValueError("Public assets cannot be symlinks")
        files[name] = path.read_bytes()
    files["robots.txt"] = robots_text(origin).encode()
    files["sitemap.xml"] = sitemap_xml(origin).encode()
    if sum(map(len, files.values())) > MAX_ARTIFACT_BYTES:
        raise ValueError("Public artifact exceeds size limit")
    sensitive_names = ("BEHEARD_STATE_API_KEY", "BEHEARD_STATE_TOKEN", "BEHEARD_EXPORT_TOKEN",
                       "BEHEARD_STATIC_DEPLOY_HOOK", "BEHEARD_FOUNDER_HASH", "BEHEARD_SESSION_SECRET")
    for key in sensitive_names:
        secret = os.environ.get(key, "").encode()
        if len(secret) >= 8 and any(secret in body for body in files.values()):
            raise ValueError("Public artifact contains a configured credential")
    return files


def pack_artifact(files):
    digest, hashes = artifact_digest(files)
    output = BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, body in sorted(files.items()):
            # Fixed timestamp keeps the artifact identical across process restarts.
            archive.writestr(zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0)), body,
                             compress_type=zipfile.ZIP_DEFLATED)
        archive.writestr(zipfile.ZipInfo("manifest.json", (2026, 1, 1, 0, 0, 0)),
                         json.dumps({"version": 1, "digest": digest, "files": hashes}, sort_keys=True))
    return digest, output.getvalue()
