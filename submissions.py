"""Private form intake with durable storage and reference-only mail notifications."""
from contextlib import closing
from datetime import datetime, timezone, timedelta
import hashlib
import json
import os
import re
import secrets
from urllib.request import Request, urlopen

from flask import abort, render_template, request
from itsdangerous import URLSafeTimedSerializer, BadSignature

KINDS = {"enquiry": "General enquiry", "volunteer": "Volunteer application", "counselling": "Counselling appointment request"}


def configure_submissions(app, connect, cloud):
    signer = URLSafeTimedSerializer(app.secret_key, salt="public-forms")
    with closing(connect(app)) as db, db:
        db.execute("""CREATE TABLE IF NOT EXISTS submissions (
            id TEXT PRIMARY KEY, kind TEXT NOT NULL, created TEXT NOT NULL,
            name TEXT NOT NULL, email TEXT NOT NULL, phone TEXT NOT NULL,
            message TEXT NOT NULL, consent TEXT NOT NULL, consent_version TEXT NOT NULL,
            fingerprint TEXT NOT NULL, notified INTEGER NOT NULL DEFAULT 0)""")

    with closing(connect(app)) as db, db:
        columns = {row[1] for row in db.execute("PRAGMA table_info(submissions)")}
        if "deleted" not in columns:
            db.execute("ALTER TABLE submissions ADD COLUMN deleted INTEGER NOT NULL DEFAULT 0")

    def notify(identifier):
        key = os.environ.get("BEHEARD_MAIL_API_KEY")
        sender = os.environ.get("BEHEARD_MAIL_FROM")
        if not key or not sender:
            return False
        body = json.dumps({
            "from": sender, "to": ["info@beheardzim.org"],
            "subject": "BeHeard website submission " + identifier,
            "text": "A new website submission is available. Sign in to the founder dashboard to read it. Reference " + identifier
        }).encode()
        req = Request("https://api.resend.com/emails", data=body, headers={
            "Authorization": "Bearer " + key, "Content-Type": "application/json",
            "Idempotency-Key": "beheard-submission-" + identifier}, method="POST")
        try:
            with urlopen(req, timeout=15) as response:
                return response.status == 200
        except Exception:
            app.logger.warning("Form notification pending")
            return False

    @app.route("/forms/<kind>", methods=["GET", "POST"])
    def public_form(kind):
        if kind not in KINDS:
            abort(404)
        if app.config.get("STATE_UNCERTAIN"):
            abort(503)
        error = None
        if request.method == "POST":
            # Render terminates HTTPS before forwarding to Flask over HTTP.
            expected_origin = ("https://" + request.host if os.environ.get("RENDER_EXTERNAL_HOSTNAME")
                               else request.host_url.rstrip("/"))
            if request.headers.get("Origin") and request.headers["Origin"] != expected_origin:
                abort(403)
            try:
                assert signer.loads(request.form.get("token", ""), max_age=7200) == kind
            except (BadSignature, AssertionError):
                abort(403)
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip()
            phone = request.form.get("phone", "").strip()
            message = request.form.get("message", "").strip()
            consent = request.form.get("consent") == "yes"
            if (not name or len(name) > 150 or len(phone) > 60 or len(message) > 3000
                    or len(email) > 254 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email)
                    or not consent or request.form.get("website")):
                error = "Check your details and consent before submitting."
            else:
                identifier = secrets.token_hex(12)
                now = datetime.now(timezone.utc).isoformat()
                fingerprint = hashlib.sha256((str(app.secret_key) + request.remote_addr).encode()).hexdigest()
                with closing(connect(app)) as db:
                    recent = db.execute("SELECT count(*) FROM submissions WHERE fingerprint=? AND created>?", (fingerprint, (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat())).fetchone()[0]
                    if recent >= 5:
                        abort(429)
                try:
                    if cloud:
                        cloud.check_revision()
                    with closing(connect(app)) as db, db:
                        db.execute("INSERT INTO submissions (id,kind,created,name,email,phone,message,consent,consent_version,fingerprint,notified) VALUES (?,?,?,?,?,?,?,?,?,?,0)",
                            (identifier, kind, now, name, email, phone, message, now, "2026-11-27", fingerprint))
                    if cloud:
                        cloud.save()
                except Exception:
                    with closing(connect(app)) as db, db:
                        db.execute("DELETE FROM submissions WHERE id=?", (identifier,))
                    if cloud:
                        try:
                            cloud.restore()
                        except Exception:
                            app.config["STATE_UNCERTAIN"] = True
                    return render_template("public_form.html", title=KINDS[kind], kind=kind,
                        error="We could not confirm your submission. Please try again or contact us.", token=signer.dumps(kind)), 503
                if notify(identifier):
                    with closing(connect(app)) as db, db:
                        db.execute("UPDATE submissions SET notified=1 WHERE id=?", (identifier,))
                    if cloud:
                        try:
                            cloud.save()
                        except Exception:
                            app.logger.warning("Notification status save pending")
                return render_template("public_form.html", title=KINDS[kind], kind=kind, reference=identifier)
        return render_template("public_form.html", title=KINDS[kind], kind=kind, error=error, token=signer.dumps(kind)), 400 if error else 200

    @app.get("/admindashboard/submissions")
    def submissions_inbox():
        with closing(connect(app)) as db:
            rows = db.execute("SELECT * FROM submissions WHERE deleted=? ORDER BY created DESC LIMIT 500", (1 if request.args.get("trash") == "1" else 0,)).fetchall()
        return render_template("submissions.html", rows=rows, kinds=KINDS, trash=request.args.get("trash") == "1")

    @app.post("/admindashboard/submissions/<identifier>/delete")
    def delete_submission(identifier):
        with closing(connect(app)) as db, db:
            db.execute("UPDATE submissions SET deleted=1 WHERE id=?", (identifier,))
        from flask import redirect
        return redirect("/admindashboard/submissions")

    @app.post("/admindashboard/submissions/<identifier>/restore")
    def restore_submission(identifier):
        with closing(connect(app)) as db, db:
            db.execute("UPDATE submissions SET deleted=0 WHERE id=?", (identifier,))
        from flask import redirect
        return redirect("/admindashboard/submissions?trash=1")

    @app.post("/admindashboard/submissions/retry")
    def retry_form_mail():
        with closing(connect(app)) as db:
            pending = db.execute("SELECT id FROM submissions WHERE notified=0 AND deleted=0 LIMIT 20").fetchall()
        for row in pending:
            if notify(row["id"]):
                with closing(connect(app)) as db, db:
                    db.execute("UPDATE submissions SET notified=1 WHERE id=?", (row["id"],))
        from flask import redirect
        return redirect("/admindashboard/submissions")

    @app.after_request
    def form_privacy(response):
        if request.path.startswith("/forms/"):
            response.headers.update({"Cache-Control": "no-store", "X-Robots-Tag": "noindex, nofollow",
                "Referrer-Policy": "same-origin", "X-Frame-Options": "DENY",
                "Content-Security-Policy": "default-src 'self'; style-src 'self'; form-action 'self'; frame-ancestors 'none'"})
        return response
