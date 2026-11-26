"""Durable-save-first static publication, with a retriable deployment outbox."""
from contextlib import closing
import hashlib
import os
import secrets
import time
from urllib.parse import parse_qs, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from flask import abort, redirect, request, url_for

from public_artifact import collect_public, pack_artifact


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def trigger_deploy(hook):
    # Never follow redirects with a credential in the URL; never log the URL.
    with build_opener(NoRedirects).open(Request(hook, data=b"", method="POST"), timeout=15) as result:
        if result.status not in (200, 202):
            raise RuntimeError("Static deployment request was rejected")


class Publication:
    def __init__(self, app, connect, cloud):
        self.app, self.connect, self.cloud = app, connect, cloud
        self.token = os.environ.get("BEHEARD_EXPORT_TOKEN", "")
        self.hook = os.environ.get("BEHEARD_STATIC_DEPLOY_HOOK", "")
        self.confirmed = None
        self.digest = None
        self.last_attempt = float("-inf")
        self.problem = None
        if self.token and (len(self.token) < 32 or not self.token.isascii() or any(c.isspace() for c in self.token)):
            raise ValueError("BEHEARD_EXPORT_TOKEN must contain at least 32 non-whitespace ASCII characters")
        if self.hook:
            parsed = urlsplit(self.hook)
            if (parsed.scheme != "https" or parsed.netloc != "api.render.com" or
                    not parsed.path.startswith("/deploy/srv-") or not parse_qs(parsed.query).get("key") or
                    parsed.fragment or not self.token):
                raise ValueError("Configure a Render static-site deploy hook and export token")
        if self.token and os.environ.get("RENDER_EXTERNAL_HOSTNAME") and not cloud:
            raise ValueError("Hosted publication requires durable cloud state")

    def prepare(self):
        return pack_artifact(collect_public(self.app)) if self.token else None

    def confirm(self, artifact):
        if artifact:
            if self.digest != artifact[0]:
                self.last_attempt = float("-inf")
            self.digest, self.confirmed = artifact

    def notify(self, force=False):
        if not self.hook or not self.confirmed:
            return
        # Include the destination so changing from staging to production enqueues it.
        target = hashlib.sha256((self.hook + self.digest).encode()).hexdigest()
        with closing(self.connect(self.app)) as db:
            row = db.execute("SELECT value FROM settings WHERE key='static_submitted'").fetchone()
        if not force and row and row[0] == target:
            return
        if not force and time.monotonic() - self.last_attempt < 60:
            return
        self.last_attempt = time.monotonic()
        try:
            trigger_deploy(self.hook)
            with closing(self.connect(self.app)) as db, db:
                db.execute("INSERT OR REPLACE INTO settings VALUES ('static_submitted',?)", (target,))
            if self.cloud:
                self.cloud.save()
            self.problem = None
        except Exception:
            # Logs must not contain HTTP exception URLs, bearer tokens or hook keys.
            self.app.logger.warning("Static deployment request not confirmed; retry is pending")
            self.problem = "Your changes are saved. The static deployment request is pending."
            with closing(self.connect(self.app)) as db, db:
                db.execute("DELETE FROM settings WHERE key='static_submitted'")

    def status(self):
        if not self.token:
            return "Static publication is not configured."
        if not self.hook:
            return "Public export is ready. Automatic static deployment is not configured."
        return self.problem or "Changes are saved; deployment requests are automatic. Check the static site before considering an update live."


def configure_publication(app, connect, cloud):
    publication = Publication(app, connect, cloud)
    app.extensions["publication"] = publication

    @app.get("/publication/artifact.zip")
    def public_export():
        authorization = request.headers.get("Authorization", "")
        expected = "Bearer " + publication.token
        if request.query_string or not publication.token or not secrets.compare_digest(authorization.encode(), expected.encode()):
            abort(404)
        if publication.confirmed is None:
            abort(503)
        if cloud:
            try:
                cloud.check_revision()
            except Exception:
                abort(503)
        return app.response_class(publication.confirmed, mimetype="application/zip", headers={
            "Cache-Control": "no-store", "X-Robots-Tag": "noindex, nofollow",
            "X-Content-Type-Options": "nosniff", "X-BeHeard-Release": publication.digest,
        })

    @app.post("/founder/publication/retry")
    def retry_publication():
        publication.notify(force=True)
        return redirect(url_for("dashboard"))

    @app.context_processor
    def publication_status():
        return {"publication_status": publication.status()}

    return publication
