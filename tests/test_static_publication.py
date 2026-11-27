"""Isolated regression tests; no live credentials, databases or deploy hooks."""
import base64
from contextlib import closing
import hashlib
from io import BytesIO
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import stat
from tempfile import TemporaryDirectory
import unittest
import warnings
from unittest.mock import MagicMock, patch
import zipfile

from werkzeug.security import generate_password_hash

from build_static import download_artifact, validate_artifact, write_site
from cloud_state import CloudState
from public_artifact import collect_public, pack_artifact
from public_manifest import PUBLIC_ASSETS, PUBLIC_FILES, PUBLIC_PAGES
from publication import NoRedirects, trigger_deploy
from publisher import ROOT, connect, create_app

TOKEN = "test-export-token-" + "x" * 40
PASSWORD = "test-password-" + "x" * 24
ORIGIN = "https://public.example.org"
HOOK = "https://api.render.com/deploy/srv-test?key=private-hook-test-key"


class FakeCloud:
    """Model a revision-checked remote snapshot without network access."""
    snapshot = None
    fail = False
    fail_restore = False
    saves = 0

    def __init__(self, private, public):
        self.private, self.public = Path(private), Path(public)

    def save(self):
        if type(self).fail:
            raise RuntimeError("simulated storage outage")
        type(self).saves += 1
        with TemporaryDirectory() as tmp:
            backup = Path(tmp) / "db"
            with closing(sqlite3.connect(self.private / "publisher.sqlite3")) as src:
                with closing(sqlite3.connect(backup)) as dest:
                    src.backup(dest)
            type(self).snapshot = (backup.read_bytes(), {p.name: p.read_bytes() for p in self.public.glob("*.html")})

    def restore(self):
        if type(self).fail_restore:
            raise RuntimeError("simulated restore outage")
        if type(self).snapshot:
            db, pages = type(self).snapshot
            (self.private / "publisher.sqlite3").write_bytes(db)
            for name, body in pages.items():
                (self.public / name).write_bytes(body)

    def check_revision(self):
        if type(self).fail_restore:
            raise RuntimeError("simulated revision outage")


class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.public, self.private = root / "public", root / "private"
        shutil.copytree(ROOT / "dist", self.public)
        self.env = patch.dict(os.environ, {
            "BEHEARD_EXPORT_TOKEN": TOKEN, "BEHEARD_STATIC_DEPLOY_HOOK": HOOK,
            "BEHEARD_PUBLIC_URL": ORIGIN, "BEHEARD_STATE_URL": "https://state.invalid",
        }, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)
        FakeCloud.snapshot, FakeCloud.fail, FakeCloud.fail_restore, FakeCloud.saves = None, False, False, 0
        self.cloud_patch = patch("cloud_state.CloudState", FakeCloud)
        self.cloud_patch.start()
        self.addCleanup(self.cloud_patch.stop)
        self.hooks = patch("publication.trigger_deploy")
        self.trigger = self.hooks.start()
        self.addCleanup(self.hooks.stop)
        self.app = create_app(self.private, self.public)
        self.app.testing = True
        with closing(connect(self.app)) as db, db:
            db.executemany("INSERT OR REPLACE INTO settings VALUES (?,?)", [
                ("password", generate_password_hash(PASSWORD)), ("generation", "test-generation")])
        self.client = self.app.test_client()
        self.trigger.reset_mock()

    def login(self):
        self.client.get("/founder/login")
        with self.client.session_transaction(path="/founder/") as s:
            csrf = s["csrf"]
        response = self.client.post("/founder/login", data={"csrf": csrf, "password": PASSWORD})
        self.assertEqual(response.status_code, 302)
        with self.client.session_transaction(path="/founder/") as s:
            return s["csrf"]

    def export(self):
        response = self.client.get("/publication/artifact.zip", headers={"Authorization": "Bearer " + TOKEN})
        self.assertEqual(response.status_code, 200)
        return response.data

    def draft(self, csrf, title="PRIVATE DRAFT SENTINEL", body="Private unapproved text"):
        response = self.client.post("/founder/edit/new", data={"csrf": csrf, "revision": "0",
            "title": title, "body": body, "day": "2026-11-26"})
        self.assertEqual(response.status_code, 302)
        return response.location.rsplit("/", 1)[1]

    def test_owner_recovery_and_submission_trash(self):
        csrf = self.login()
        with closing(connect(self.app)) as db, db:
            db.execute("INSERT INTO submissions (id,kind,created,name,email,phone,message,consent,consent_version,fingerprint) VALUES (?,?,?,?,?,?,?,?,?,?)",
                ("trash-test", "enquiry", "2026-11-27", "Test", "test@example.org", "", "Test message", "yes", "1", "test"))
        self.assertEqual(self.client.post("/founder/submissions/trash-test/delete", data={"csrf": csrf}).status_code, 302)
        self.assertNotIn(b"Test message", self.client.get("/founder/submissions").data)
        self.assertIn(b"Test message", self.client.get("/founder/submissions?trash=1").data)
        self.client.post("/founder/submissions/trash-test/restore", data={"csrf": csrf})
        self.assertIn(b"Test message", self.client.get("/founder/submissions").data)
        self.client.post("/founder/logout", data={"csrf": csrf})
        self.client.get("/founder/recover")
        with self.client.session_transaction(path="/founder/") as state:
            csrf = state["csrf"]
        code = "owner-recovery-test-" + "x" * 30
        with patch.dict(os.environ, {"BEHEARD_OWNER_RECOVERY_HASH": generate_password_hash(code)}):
            response = self.client.post("/founder/recover", data={"csrf": csrf, "recovery_code": code,
                "new_password": "replacement-password-long", "confirm_password": "replacement-password-long"})
        self.assertEqual(response.status_code, 302)
        self.assertIn("password_changed", response.location)

    def test_admin_password_change(self):
        csrf = self.login()
        changed = "new-password-" + "z" * 25
        response = self.client.post("/founder/password", data={
            "csrf": csrf, "current_password": PASSWORD,
            "new_password": changed, "confirm_password": changed})
        self.assertEqual(response.status_code, 302)
        self.assertIn("password_changed", response.location)
        self.assertEqual(self.client.get("/founder/").status_code, 302)
        self.client.get("/founder/login")
        with self.client.session_transaction(path="/founder/") as session:
            csrf = session["csrf"]
        response = self.client.post("/founder/login", data={"csrf": csrf, "password": changed})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.get("/founder/password").status_code, 200)

    def test_export_matches_every_live_page_and_preserves_all_media(self):
        files, digest = validate_artifact(self.export(), ORIGIN)
        for name in PUBLIC_PAGES:
            response = self.client.get("/" if name == "index.html" else "/" + name)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(files[name].replace(b"\r\n", b"\n"), response.data.replace(b"\r\n", b"\n"))
            response.close()
        for name in PUBLIC_ASSETS:
            self.assertEqual(files[name], (self.public / name).read_bytes())
        self.assertIn(b'home-news-shortcut', files["index.html"])
        self.assertIn(b'Children', files["index.html"])
        self.assertIn(b'sewing-story-1.jpg', files["gallery.html"])
        self.assertEqual(len(digest), 64)
        self.assertTrue(self.export() == self.export(), "Export changed without a public edit")

    def test_private_state_and_drafts_never_export_or_trigger_deploy(self):
        csrf = self.login()
        before = self.export()
        (self.public / "secret.env").write_text("PRIVATE FILE SENTINEL")
        (self.public / "private.jpg").write_bytes(b"PRIVATE MEDIA SENTINEL")
        self.draft(csrf)
        self.assertTrue(before == self.export(), "A draft changed the public export")
        self.trigger.assert_not_called()
        files, _ = validate_artifact(before, ORIGIN)
        exported = b"".join(files.values())
        for sentinel in (b"PRIVATE", TOKEN.encode(), PASSWORD.encode(), b"test-generation", b"publisher.sqlite3"):
            self.assertNotIn(sentinel, exported)
        for path in ("/secret.env", "/private.jpg", "/.beheard/publisher.sqlite3", "/templates/founder.html"):
            self.assertEqual(self.client.get(path).status_code, 404)
        self.assertNotIn("editor.js", files)

    def test_publish_edit_and_withdraw_and_escaping(self):
        csrf = self.login()
        item = self.draft(csrf, title="Approved <title>", body="Approved <script>alert(1)</script>")
        self.client.post("/founder/status/" + item, data={"csrf": csrf, "revision": 1, "action": "publish"})
        self.assertEqual(self.trigger.call_count, 1)
        files, _ = validate_artifact(self.export(), ORIGIN)
        for name in ("index.html", "stories.html"):
            self.assertIn(b"Approved &lt;title&gt;", files[name])
            self.assertNotIn(b"<script>alert(1)", files[name])
        response = self.client.post("/founder/edit/" + item, data={"csrf": csrf, "revision": 1,
            "title": "UNPUBLISHED REVISION", "body": "Keep me private", "day": "2026-11-26"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.trigger.call_count, 1)
        files, _ = validate_artifact(self.export(), ORIGIN)
        self.assertNotIn(b"UNPUBLISHED REVISION", files["stories.html"])
        self.client.post("/founder/status/" + item, data={"csrf": csrf, "revision": 2, "action": "withdraw"})
        files, _ = validate_artifact(self.export(), ORIGIN)
        self.assertNotIn(b"Approved &lt;title&gt;", files["stories.html"])
        self.assertEqual(self.trigger.call_count, 2)
        with closing(connect(self.app)) as db:
            self.assertEqual(db.execute("SELECT title FROM draft WHERE id=?", (item,)).fetchone()[0], "UNPUBLISHED REVISION")

    def test_page_save_and_stale_revision_and_csrf(self):
        csrf = self.login()
        old = (self.public / "about.html").read_text("utf-8")
        version = hashlib.sha256(old.encode()).hexdigest()
        data = {"csrf": csrf, "page": "about.html", "version": version, "text_0": "An approved edited description."}
        response = self.client.post("/founder/pages", data=data)
        self.assertEqual(response.status_code, 302)
        self.trigger.assert_called_once()
        files, _ = validate_artifact(self.export(), ORIGIN)
        self.assertIn(b"An approved edited description.", files["about.html"])
        self.assertEqual(self.client.post("/founder/pages", data=data).status_code, 409)
        self.assertEqual(self.client.post("/founder/pages", data={**data, "csrf": "wrong"}).status_code, 403)
        self.assertEqual(self.app.test_client().post("/founder/publication/retry").status_code, 403)

    def test_storage_failure_keeps_previous_export_and_durable_state(self):
        csrf = self.login()
        item = self.draft(csrf)
        before = self.export()
        FakeCloud.fail = True
        response = self.client.post("/founder/status/" + item, data={"csrf": csrf, "revision": 1, "action": "publish"})
        self.assertEqual(response.status_code, 503)
        self.assertTrue(before == self.export(), "A failed save changed the public export")
        self.trigger.assert_not_called()
        with closing(connect(self.app)) as db:
            self.assertIsNone(db.execute("SELECT * FROM published WHERE id=?", (item,)).fetchone())

    def test_hook_failure_is_saved_and_retried_after_restart(self):
        csrf = self.login()
        item = self.draft(csrf, title="Approved durable update")
        self.trigger.side_effect = RuntimeError("test")
        response = self.client.post("/founder/status/" + item, data={"csrf": csrf, "revision": 1, "action": "publish"})
        self.assertEqual(response.status_code, 302)
        self.assertIn(b"pending", self.client.get("/founder/").data)
        self.trigger.side_effect = None
        fresh = create_app(self.private, self.public)
        with fresh.test_client().get("/stories.html") as response:
            self.assertIn(b"Approved durable update", response.data)
        self.assertEqual(self.trigger.call_count, 2)
        files, _ = validate_artifact(self.export(), ORIGIN)
        self.assertIn(b"Approved durable update", files["stories.html"])

    def test_export_auth_and_admin_noindex(self):
        for headers in ({}, {"Authorization": "Bearer wrong"}, {"Authorization": "Bearer " + TOKEN + "x"}):
            self.assertEqual(self.client.get("/publication/artifact.zip", headers=headers).status_code, 404)
        self.assertEqual(self.client.get("/publication/artifact.zip?token=" + TOKEN).status_code, 404)
        self.assertEqual(self.client.get("/publication/artifact.zip?token=" + TOKEN,
            headers={"Authorization": "Bearer " + TOKEN}).status_code, 404)
        self.assertEqual(self.client.get("/founder/login").headers["X-Robots-Tag"], "noindex, nofollow")
        self.assertEqual(self.client.get("/index.html").status_code, 301)
        self.app.config["ADMIN_ONLY"] = True
        self.assertIn(b"Disallow: /", self.client.get("/robots.txt").data)
        self.assertEqual(self.client.get("/").headers["X-Robots-Tag"], "noindex, nofollow")
        self.assertEqual(self.client.get("/").location, ORIGIN + "/")
        self.assertEqual(self.client.get("/stories.html").location, ORIGIN + "/stories.html")
        self.assertEqual(self.client.get("/healthz").status_code, 200)
        self.assertEqual(self.client.get("/founder/login").status_code, 200)

    def test_build_atomic_and_staging_noindex_and_no_stale_fallback(self):
        output = Path(self.tmp.name) / "build"
        write_site(self.export(), output, ORIGIN, staging=True)
        self.assertEqual(set(p.name for p in output.iterdir()), PUBLIC_FILES | {"release.json"})
        self.assertIn(b'noindex, nofollow', (output / "index.html").read_bytes())
        self.assertIn(b"Disallow: /", (output / "robots.txt").read_bytes())
        with self.assertRaises(ValueError):
            write_site(self.export(), output, ORIGIN)
        with self.assertRaises(ValueError):
            validate_artifact(self.export(), "https://wrong.example.org")

    def test_tampered_private_traversal_duplicate_and_symlink_archives_rejected(self):
        original = self.export()
        for extra in ("../escape", ".env", "publisher.sqlite3", "editor.js", "index.html"):
            output = BytesIO(original)
            with warnings.catch_warnings(), zipfile.ZipFile(output, "a") as archive:
                warnings.simplefilter("ignore", UserWarning)
                archive.writestr(extra, b"private")
            with self.assertRaises(ValueError):
                validate_artifact(output.getvalue(), ORIGIN)
        files, _ = validate_artifact(original, ORIGIN)
        digest, packed = pack_artifact({**files, "index.html": files["index.html"] + b"tampered"})
        # Valid new manifest still has to pass the expected origin check.
        with self.assertRaises(ValueError):
            validate_artifact(packed, "https://wrong.example.org")
        output = BytesIO()
        with zipfile.ZipFile(BytesIO(original)) as src, zipfile.ZipFile(output, "w") as dst:
            for info in src.infolist():
                content = src.read(info.filename)
                if info.filename == "site.js":
                    content += b"tampered"
                dst.writestr(info, content)
        with self.assertRaises(ValueError):
            validate_artifact(output.getvalue(), ORIGIN)
        output = BytesIO()
        with zipfile.ZipFile(BytesIO(original)) as src, zipfile.ZipFile(output, "w") as dst:
            for info in src.infolist():
                content = src.read(info.filename)
                if info.filename == "site.js":
                    info.create_system = 3
                    info.external_attr = (stat.S_IFLNK | 0o777) << 16
                dst.writestr(info, content)
        with self.assertRaises(ValueError):
            validate_artifact(output.getvalue(), ORIGIN)

    def test_manual_retry_can_repeat_an_accepted_but_failed_build(self):
        csrf = self.login()
        response = self.client.post("/founder/publication/retry", data={"csrf": csrf})
        self.assertEqual(response.status_code, 302)
        self.trigger.assert_called_once()

    def test_failed_save_and_failed_restore_block_exports_and_further_edits(self):
        csrf = self.login()
        item = self.draft(csrf)
        FakeCloud.fail, FakeCloud.fail_restore = True, True
        response = self.client.post("/founder/status/" + item, data={"csrf": csrf, "revision": 1, "action": "publish"})
        self.assertEqual(response.status_code, 503)
        self.assertEqual(self.client.get("/publication/artifact.zip", headers={"Authorization": "Bearer " + TOKEN}).status_code, 503)
        self.assertEqual(self.client.get("/founder/").status_code, 503)
        self.assertEqual(self.client.post("/founder/publication/retry", data={"csrf": csrf}).status_code, 503)
        self.trigger.assert_not_called()

    def test_export_rejects_retiring_or_unreachable_storage_instance(self):
        with patch.object(self.app.extensions["publication"].cloud, "check_revision", side_effect=RuntimeError("changed")):
            response = self.client.get("/publication/artifact.zip", headers={"Authorization": "Bearer " + TOKEN})
            self.assertEqual(response.status_code, 503)

    def test_unchanged_restart_does_not_trigger_another_deploy(self):
        before = self.export()
        fresh = create_app(self.private, self.public)
        self.trigger.assert_not_called()
        response = fresh.test_client().get("/publication/artifact.zip", headers={"Authorization": "Bearer " + TOKEN})
        self.assertTrue(before == response.data, "An unchanged restart altered the artifact")

    def test_uploaded_photos_are_embedded_and_private_until_publication(self):
        from PIL import Image
        photo = BytesIO()
        Image.new("RGB", (8, 8), (30, 40, 50)).save(photo, format="PNG")
        photo.seek(0)
        csrf = self.login()
        before = self.export()
        response = self.client.post("/founder/edit/new", data={"csrf": csrf, "revision": 0,
            "title": "Approved image update", "body": "Approved photograph text", "day": "2026-11-26",
            "photo": (photo, "approved.png"), "alt": "Approved photo description"})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(before == self.export(), "A draft photo appeared in the public artifact")
        item = response.location.rsplit("/", 1)[1]
        self.client.post("/founder/status/" + item, data={"csrf": csrf, "revision": 1, "action": "publish"})
        files, _ = validate_artifact(self.export(), ORIGIN)
        self.assertIn(b'data:image/jpeg;base64,', files["stories.html"])
        self.assertIn(b'Approved photo description', files["index.html"])

    def test_founder_password_failures_logout_and_private_previews(self):
        self.client.get("/founder/login")
        with self.client.session_transaction(path="/founder/") as session:
            csrf = session["csrf"]
        response = self.client.post("/founder/login", data={"csrf": csrf, "password": "wrong"})
        self.assertEqual(response.status_code, 401)
        csrf = self.login()
        item = self.draft(csrf)
        private = self.client.get("/founder/preview/" + item)
        self.assertIn(b"PRIVATE DRAFT SENTINEL", private.data)
        self.assertEqual(private.headers["Cache-Control"], "no-store")
        self.assertEqual(private.headers["X-Robots-Tag"], "noindex, nofollow")
        self.client.post("/founder/logout", data={"csrf": csrf})
        self.assertEqual(self.client.get("/founder/preview/" + item).status_code, 302)
        self.assertEqual(self.client.post("/founder/status/" + item, data={"csrf": csrf, "revision": 1, "action": "publish"}).status_code, 403)

    def test_configured_secret_in_public_file_blocks_export(self):
        (self.public / "about.html").write_text(TOKEN, encoding="utf-8")
        with self.assertRaises(ValueError):
            collect_public(self.app)

    def test_download_refuses_insecure_and_credential_urls(self):
        for url in ("http://admin.example.org/publication/artifact.zip", "https://user:pass@admin.example.org/publication/artifact.zip",
                    "https://admin.example.org/publication/artifact.zip?token=secret", "https://admin.example.org/"):
            with self.assertRaises(ValueError):
                download_artifact(url, TOKEN)


class CloudContractTests(unittest.TestCase):
    def test_snapshot_restore_preserves_credentials_drafts_pages_and_revision_cas(self):
        with TemporaryDirectory() as tmp, patch.dict(os.environ, {
            "BEHEARD_STATE_URL": "https://state.invalid", "BEHEARD_STATE_API_KEY": "test-key", "BEHEARD_STATE_TOKEN": "test-token"}):
            root = Path(tmp)
            private, public = root / "private", root / "public"
            private.mkdir(); public.mkdir()
            with closing(sqlite3.connect(private / "publisher.sqlite3")) as db, db:
                db.execute("CREATE TABLE private (credential TEXT, draft TEXT)")
                db.execute("INSERT INTO private VALUES ('original password hash', 'private draft')")
            (public / "about.html").write_text('<p>Edited text and embedded photo data</p>', encoding="utf-8")
            cloud = CloudState(private, public)
            cloud.revision = 41
            with patch.object(cloud, "request", return_value=[{"revision": 42}]) as remote:
                cloud.save()
            args = remote.call_args.args
            self.assertEqual(args[0:2], ("PATCH", "?id=eq.1&revision=eq.41"))
            payload = args[2]["payload"]
            self.assertEqual(set(payload), {"database", "pages"})
            (public / "about.html").write_text("lost local copy")
            with patch.object(cloud, "request", return_value=[{"revision": 42, "payload": payload}]):
                cloud.restore()
            self.assertEqual(cloud.revision, 42)
            with patch.object(cloud, "request", return_value=[{"revision": 42}]):
                cloud.check_revision()
            for rows in ([], [{"revision": 43}]):
                with patch.object(cloud, "request", return_value=rows), self.assertRaises(RuntimeError):
                    cloud.check_revision()
            self.assertEqual((public / "about.html").read_text(), payload["pages"]["about.html"])
            with closing(sqlite3.connect(private / "publisher.sqlite3")) as db:
                self.assertEqual(db.execute("SELECT * FROM private").fetchone(), ("original password hash", "private draft"))
            with patch.object(cloud, "request", return_value=[]), self.assertRaises(RuntimeError):
                cloud.save()
            self.assertEqual(cloud.revision, 42)


class TransportTests(unittest.TestCase):
    def test_bearer_is_only_in_header_and_redirects_are_disabled(self):
        response = MagicMock()
        response.__enter__.return_value = response
        response.status = 200
        response.read.return_value = b"public artifact"
        with patch("build_static.build_opener") as factory:
            factory.return_value.open.return_value = response
            body = download_artifact("https://admin.example.org/publication/artifact.zip", TOKEN)
            self.assertEqual(body, b"public artifact")
            req = factory.return_value.open.call_args.args[0]
            self.assertEqual(req.get_header("Authorization"), "Bearer " + TOKEN)
            self.assertNotIn(TOKEN, req.full_url)
            redirect_handler = factory.call_args.args[0]()
            self.assertIsNone(redirect_handler.redirect_request(None, None, 302, None, None, "https://elsewhere.invalid"))

    def test_hook_accepts_started_and_queued_responses(self):
        for code in (200, 202):
            response = MagicMock()
            response.__enter__.return_value = response
            response.status = code
            with patch("publication.build_opener") as factory:
                factory.return_value.open.return_value = response
                trigger_deploy(HOOK)
                req = factory.return_value.open.call_args.args[0]
                self.assertEqual(req.get_method(), "POST")
                self.assertTrue(issubclass(factory.call_args.args[0], NoRedirects))


if __name__ == "__main__":
    unittest.main()
