"""Fetch and verify a confirmed public export. No Flask or Supabase access needed."""
import argparse
from io import BytesIO
import json
import os
from pathlib import Path
import re
import stat
from tempfile import TemporaryDirectory
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
import zipfile

from public_manifest import PUBLIC_FILES, PUBLIC_PAGES, MAX_ARTIFACT_BYTES, artifact_digest


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def download_artifact(url, token):
    parsed = urlsplit(url)
    if (parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password or
            parsed.query or parsed.fragment or parsed.path != "/publication/artifact.zip"):
        raise ValueError("Export URL must be an HTTPS /publication/artifact.zip endpoint")
    if len(token) < 32 or not token.isascii() or any(c.isspace() for c in token):
        raise ValueError("Configure the private export token")
    req = Request(url, headers={"Authorization": "Bearer " + token})
    with build_opener(NoRedirects).open(req, timeout=180) as response:
        if response.status != 200:
            raise ValueError("Export unavailable")
        body = response.read(MAX_ARTIFACT_BYTES + 1)
    if len(body) > MAX_ARTIFACT_BYTES:
        raise ValueError("Export exceeds size limit")
    return body


def validate_artifact(body, origin):
    parsed = urlsplit(origin)
    if (parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password or
            parsed.path or parsed.query or parsed.fragment):
        raise ValueError("Configure the canonical HTTPS public origin")
    if len(body) > MAX_ARTIFACT_BYTES:
        raise ValueError("Export exceeds size limit")
    with zipfile.ZipFile(BytesIO(body)) as archive:
        infos = archive.infolist()
        names = [item.filename for item in infos]
        if len(names) != len(set(names)) or set(names) != PUBLIC_FILES | {"manifest.json"}:
            raise ValueError("Export contains missing, duplicate or unapproved files")
        if sum(item.file_size for item in infos) > MAX_ARTIFACT_BYTES:
            raise ValueError("Expanded export exceeds size limit")
        for item in infos:
            if stat.S_ISLNK(item.external_attr >> 16) or item.is_dir() or item.flag_bits & 1:
                raise ValueError("Export contains an unsafe entry")
        manifest = json.loads(archive.read("manifest.json"))
        files = {name: archive.read(name) for name in PUBLIC_FILES}
    digest, hashes = artifact_digest(files)
    if manifest != {"version": 1, "digest": digest, "files": hashes}:
        raise ValueError("Export integrity check failed")
    for name in PUBLIC_PAGES:
        page = files[name].decode("utf-8")
        canonical = origin + ("/" if name == "index.html" else "/" + name)
        if page.count('<link rel="canonical" href="' + canonical + '">') != 1:
            raise ValueError("Export canonical origin differs from configuration")
        # No application backend calls belong in the static document.
        if re.search(r'(?:src|href|action)=[\"\']/(?:founder/|publication/|\.beheard/)', page, re.I):
            raise ValueError("Export references a private route")
    return files, digest


def write_site(body, output, origin, staging=False):
    files, digest = validate_artifact(body, origin)
    output = Path(output).resolve()
    if output.exists():
        raise ValueError("Output must not exist; use a fresh build directory")
    output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".beheard-build-", dir=output.parent) as temp:
        root = Path(temp) / "site"
        root.mkdir()
        if staging:
            files["robots.txt"] = b"User-agent: *\nDisallow: /\n"
            for name in PUBLIC_PAGES:
                files[name] = files[name].replace(b"</head>", b'<meta name="robots" content="noindex, nofollow"></head>', 1)
        for name, content in files.items():
            (root / name).write_bytes(content)
        (root / "release.json").write_text(json.dumps({"digest": digest, "staging": staging}), encoding="utf-8")
        os.replace(root, output)
    return digest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", type=Path, help="Offline public-only export for local verification")
    parser.add_argument("--output", type=Path, default=Path("public-build"))
    args = parser.parse_args()
    try:
        body = args.artifact.read_bytes() if args.artifact else download_artifact(
            os.environ["BEHEARD_EXPORT_URL"], os.environ["BEHEARD_EXPORT_TOKEN"])
        digest = write_site(body, args.output, os.environ["BEHEARD_PUBLIC_URL"].rstrip("/"),
                            staging=os.environ.get("BEHEARD_STATIC_STAGING") == "1")
    except Exception:
        # HTTP exceptions include URLs: never print credentials or traceback here.
        raise SystemExit("Static build failed verification. Previous deployment remains unchanged.") from None
    print("Verified public release " + digest)


if __name__ == "__main__":
    main()
