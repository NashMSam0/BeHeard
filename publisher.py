"""Founder-only local editor. Run 'python publisher.py setup' to set the password."""

import argparse

import base64

from contextlib import closing

from datetime import date, timedelta

from getpass import getpass

from io import BytesIO

import os

import re

import html

from pathlib import Path

import secrets

import sqlite3

from tempfile import NamedTemporaryFile

import time

from uuid import uuid4



from flask import Flask, abort, redirect, render_template, request, session, url_for

from PIL import Image, ImageOps, UnidentifiedImageError

from werkzeug.security import check_password_hash, generate_password_hash



ROOT = Path(__file__).resolve().parent

START = "<!-- published news -->"

END = "<!-- end published news -->"





def connect(app):

    db = sqlite3.connect(app.config["DATABASE"], timeout=15)

    db.row_factory = sqlite3.Row

    return db





def publish_page(app, db):

    """Replace only the news block, keeping the rest of the editable page."""

    page = Path(app.static_folder) / "stories.html"

    original = page.read_text(encoding="utf-8")

    if original.count(START) != 1 or original.count(END) != 1:

        raise RuntimeError("Missing news markers in stories.html")

    before, block = original.split(START)

    _, after = block.split(END)

    live = db.execute("SELECT * FROM published ORDER BY day DESC, id")

    with app.app_context():

        html = render_template("articles.html", articles=live)

    updated = before + START + html + END + after

    if updated != original:

        with NamedTemporaryFile(mode="w", encoding="utf-8", dir=page.parent,

                               suffix=".tmp", delete=False) as temp:

            temp.write(updated)

        try:

            os.replace(temp.name, page)

        finally:

            Path(temp.name).unlink(missing_ok=True)





def photograph(upload):

    if not upload or not upload.filename:

        return None

    try:

        with Image.open(upload.stream, formats=["JPEG", "PNG", "WEBP"]) as image:

            if image.width * image.height > 20000000:

                abort(400, "Choose a smaller photograph.")

            image.thumbnail((1280, 1280))

            photo = ImageOps.exif_transpose(image).convert("RGB")

            output = BytesIO()

            photo.save(output, format="JPEG", quality=80)

    except (UnidentifiedImageError, OSError, Image.DecompressionBombError, ValueError):

        abort(400, "Choose a JPEG, PNG or WebP photograph.")

    return base64.b64encode(output.getvalue()).decode("ascii")





def create_app(private=None, public=None):

    storage = os.environ.get("BEHEARD_DATA_DIR")
    private = Path(private or (Path(storage) / "private" if storage else ROOT / ".beheard"))

    private.mkdir(parents=True, exist_ok=True)

    public = Path(public or (Path(storage) / "public" if storage else ROOT / "dist"))
    if storage:
        public.mkdir(parents=True, exist_ok=True)
        # Preserve edited HTML across deploys; refresh application styles and scripts.
        import shutil
        for asset in (ROOT / "dist").iterdir():
            if asset.is_file() and (asset.suffix != ".html" or not (public / asset.name).exists()):
                shutil.copy2(asset, public / asset.name)
    app = Flask(__name__, static_folder=str(public), static_url_path="")

    app.config.update(DATABASE=private / "publisher.sqlite3", MAX_CONTENT_LENGTH=100*1024*1024,

                      TRUSTED_HOSTS=["localhost", "127.0.0.1"], SESSION_COOKIE_NAME="beheard_founder",

                      SESSION_COOKIE_PATH="/founder", SESSION_COOKIE_SAMESITE="Strict",

                      PERMANENT_SESSION_LIFETIME=timedelta(hours=4))

    host = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
    if host:
        app.config["TRUSTED_HOSTS"].append(host)
        app.config["SESSION_COOKIE_SECURE"] = True
    domains = os.environ.get("BEHEARD_DOMAINS", "")
    app.config["TRUSTED_HOSTS"].extend(d.strip() for d in domains.split(",") if d.strip())

    cloud = None
    if os.environ.get("BEHEARD_STATE_URL"):
        from cloud_state import CloudState
        cloud = CloudState(private, public)
        cloud.restore()

    with closing(connect(app)) as db, db:

        db.executescript("""

            CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);

            CREATE TABLE IF NOT EXISTS draft (

              id TEXT PRIMARY KEY, revision INTEGER, title TEXT, day TEXT, body TEXT, photo TEXT, alt TEXT);

            CREATE TABLE IF NOT EXISTS published (

              id TEXT PRIMARY KEY, revision INTEGER, title TEXT, day TEXT, body TEXT, photo TEXT, alt TEXT);

            CREATE TABLE IF NOT EXISTS failures (at INTEGER);

        """)

        db.execute("INSERT OR IGNORE INTO settings VALUES ('secret',?)", (secrets.token_hex(32),))

        bootstrap = os.environ.get("BEHEARD_FOUNDER_HASH")
        if bootstrap and not db.execute("SELECT 1 FROM settings WHERE key='password'").fetchone():
            db.executemany("INSERT OR REPLACE INTO settings VALUES (?,?)", [
                ("password", bootstrap),
                ("generation", os.environ["BEHEARD_FOUNDER_GENERATION"]),
                ("secret", os.environ["BEHEARD_SESSION_SECRET"])])
        app.secret_key = db.execute("SELECT value FROM settings WHERE key='secret'").fetchone()[0]

        db.execute("SELECT 1")

        publish_page(app, db)



    if cloud:
        cloud.save()

    @app.after_request
    def persist_changes(response):
        if cloud and request.method == "POST" and request.path.startswith("/founder"):
            if response.status_code < 400 or request.endpoint == "login":
                try:
                    cloud.save()
                except Exception:
                    app.logger.exception("Could not confirm cloud save")
                    try:
                        cloud.restore()
                    except Exception:
                        app.logger.exception("Cloud restore unavailable")
                    return app.response_class("We could not confirm the save. Reopen the editor and check your content before retrying.", status=503)
        if request.path.endswith(".html") or request.path == "/":
            response.headers["Cache-Control"] = "no-cache"
        return response

    @app.errorhandler(413)
    def upload_too_large(error):
        return render_template("upload_error.html"), 413

    @app.before_request

    def founder_only():

        if not request.path.startswith("/founder"):

            return

        if request.method == "POST":

            expected = session.get("csrf", "")

            if not expected or not secrets.compare_digest(request.form.get("csrf", "").encode(), expected.encode()):

                abort(403)

        if request.endpoint == "login":

            return

        with closing(connect(app)) as db:

            account = db.execute("SELECT value FROM settings WHERE key='generation'").fetchone()

        if not account or session.get("account") != account[0]:

            if request.method == "POST":

                abort(403)

            return redirect(url_for("login"))



    @app.after_request

    def headers(response):

        if request.path.startswith("/founder"):

            response.headers.update({"Cache-Control":"no-store", "X-Frame-Options":"DENY",

                "Referrer-Policy":"no-referrer", "X-Content-Type-Options":"nosniff",

                "Content-Security-Policy":"default-src 'self'; img-src 'self' data: blob:; frame-ancestors 'none'; form-action 'self'; base-uri 'none'"})

        return response



    @app.get("/healthz")
    def health():
        with closing(connect(app)) as db:
            db.execute("SELECT 1")
        return {"status": "ok"}

    @app.route("/")

    def home():

        return app.send_static_file("index.html")



    @app.route("/founder/login", methods=["GET", "POST"])

    def login():

        session.setdefault("csrf", secrets.token_hex(24))

        with closing(connect(app)) as db, db:

            settings = dict(db.execute("SELECT key,value FROM settings"))

            if request.method == "POST" and "password" in settings:

                now = int(time.time())

                db.execute("DELETE FROM failures WHERE at < ?", (now-300,))

                if db.execute("SELECT COUNT(*) FROM failures").fetchone()[0] >= 8:

                    abort(429, "Try again in five minutes.")

                if check_password_hash(settings["password"], request.form.get("password","")):

                    session.clear()

                    session.permanent = True

                    session.update(account=settings["generation"], csrf=secrets.token_hex(24))

                    db.execute("DELETE FROM failures")

                    return redirect(url_for("dashboard"))

                db.execute("INSERT INTO failures VALUES (?)", (now,))

                return render_template("founder.html", view="login", ready=True, error="Password incorrect."), 401

        return render_template("founder.html", view="login", ready="password" in settings)



    @app.post("/founder/logout")

    def logout():

        session.clear()

        return redirect(url_for("login"))



    @app.get("/founder/")

    def dashboard():

        with closing(connect(app)) as db:

            rows = db.execute("""SELECT d.id,d.title,d.day,d.revision,p.revision AS live

                FROM draft d LEFT JOIN published p USING(id) ORDER BY d.day DESC, d.rowid DESC""").fetchall()

        return render_template("founder.html", view="list", rows=rows)



    @app.route("/founder/edit/<item>", methods=["GET","POST"])

    def edit(item):

        with closing(connect(app)) as db, db:

            if request.method == "POST":

                db.execute("BEGIN IMMEDIATE")

            row = db.execute("SELECT * FROM draft WHERE id=?", (item,)).fetchone()

            if item != "new" and not row:

                abort(404)

            if request.method == "GET":

                return render_template("founder.html", view="edit", row=row, today=date.today().isoformat())

            revision = row["revision"] if row else 0

            if request.form.get("revision",type=int) != revision:

                abort(409, "This draft has changed. Reopen it before saving.")

            title, body, alt = (request.form.get(k,"").strip() for k in ("title","body","alt"))

            if not title or not body or len(title)>180 or len(body)>30000 or len(alt)>300:

                abort(400, "Check the title, text and photo description.")

            try:

                day = date.fromisoformat(request.form.get("day","")).isoformat()

            except ValueError:

                abort(400, "Choose a valid date.")

            photo = photograph(request.files.get("photo"))

            if photo is None and row and not request.form.get("remove_photo"):

                photo = row["photo"]

            if photo and not alt:

                abort(400, "Describe the photograph before saving.")

            if item == "new":

                item = uuid4().hex

            db.execute("INSERT OR REPLACE INTO draft VALUES (?,?,?,?,?,?,?)",

                       (item,revision+1,title,day,body,photo,alt if photo else ""))

        return redirect(url_for("preview", item=item))



    @app.get("/founder/preview/<item>")

    def preview(item):

        with closing(connect(app)) as db:

            row = db.execute("SELECT * FROM draft WHERE id=?", (item,)).fetchone()

            live = db.execute("SELECT revision FROM published WHERE id=?", (item,)).fetchone()

        if not row:

            abort(404)

        return render_template("founder.html", view="preview", row=row, live=live)



    @app.post("/founder/status/<item>")

    def status(item):

        with closing(connect(app)) as db, db:

            db.execute("BEGIN IMMEDIATE")

            row = db.execute("SELECT revision FROM draft WHERE id=?", (item,)).fetchone()

            if not row:

                abort(404)

            if row[0] != request.form.get("revision",type=int):

                abort(409, "Reopen the preview before publishing.")

            action = request.form.get("action")

            if action == "publish":

                db.execute("INSERT OR REPLACE INTO published SELECT * FROM draft WHERE id=?", (item,))

            elif action == "withdraw":

                db.execute("DELETE FROM published WHERE id=?", (item,))

            else:

                abort(400)

            publish_page(app, db)

        return redirect(url_for("dashboard"))



    @app.route("/founder/pages", methods=["GET", "POST"])

    def pages():

        names = {"index.html": "Home", "about.html": "About", "programmes.html": "Programmes", "stories.html": "Stories", "involved.html": "Donations and volunteering", "contact.html": "Contact", "privacy.html": "Privacy"}

        name = request.values.get("page", "index.html")

        if name not in names:

            abort(404)

        path = Path(app.static_folder) / name

        source = path.read_text("utf-8")

        slide_block = re.search(r'<!-- home slides -->(.*?)<!-- end home slides -->', source, re.S)
        current_slides = re.findall(r'<img\b[^>]*>', slide_block[1]) if slide_block else []
        page_block = re.search(r'<figure class="page-photo">(.*?)</figure>', source, re.S)
        current_photo = None
        if page_block:
            image = re.search(r'src="([^"]+)"', page_block[1])
            if image:
                current_photo = html.unescape(image[1])
        slide_previews = []
        for image in current_slides:
            src = re.search(r'src="([^"]+)"', image)
            if src:
                slide_previews.append(html.unescape(src[1]))
        pattern = r"<(p)([^>]*)>([^<>]+)</\1>"

        # News is managed by its dedicated draft and publishing workflow.

        news_start = source.find(START)

        news_end = source.find(END)

        matches = [m for m in re.finditer(pattern, source)

                   if 'kicker' not in m[2] and not (news_start >= 0 and news_start < m.start() < news_end)]

        fields = []

        counts = {}

        for match in matches:

            headings = list(re.finditer(r"<h[123][^>]*>(.*?)</h[123]>", source[:match.start()], re.S))

            heading = html.unescape(re.sub(r"<[^>]+>", "", headings[-1][1])) if headings else names[name]

            counts[heading] = counts.get(heading, 0) + 1

            label = heading + (" — description" if counts[heading] == 1 else " — additional details")

            fields.append({"label": label, "text": html.unescape(match[3])})

        if request.method == "POST":

            import hashlib

            if request.form.get("version") != hashlib.sha256(source.encode()).hexdigest():

                abort(409, "Page changed. Reopen before saving.")

            for index, match in reversed(list(enumerate(matches))):

                value = request.form.get("text_"+str(index), html.unescape(match[3])).strip()

                if not value or len(value)>30000:

                    abort(400)

                source = source[:match.start(3)] + html.escape(value) + source[match.end(3):]

            photo = photograph(request.files.get("photo"))

            if photo:

                alt = request.form.get("alt", "").strip()

                if not alt:

                    abort(400, "Describe the photograph.")

                image = '<figure class="page-photo"><img alt="'+html.escape(alt, quote=True)+'" src="data:image/jpeg;base64,'+photo+'"></figure>'

                source = re.sub(r'<figure class="page-photo">.*?</figure>', '', source, flags=re.S)

                source = source.replace('</main>', image+'</main>')

            if request.form.get("remove"):

                source = re.sub(r'<figure class="page-photo">.*?</figure>', '', source, flags=re.S)

            if name == "index.html" and request.form.getlist("remove_slide") and slide_block:
                removals = set(request.form.getlist("remove_slide"))
                kept = [image for i, image in enumerate(current_slides) if str(i) not in removals]
                if kept:
                    content = '<div class="home-slideshow"><div class="slide-track">' + ''.join(kept) + '</div><button class="slideshow-toggle" type="button">Pause photographs</button></div>'
                    replacement = '<!-- home slides -->' + content + '<!-- end home slides -->'
                else:
                    replacement = ''
                source = re.sub(r'<!-- home slides -->.*?<!-- end home slides -->', lambda m: replacement, source, flags=re.S)
            if name == "index.html":

                uploads = [f for f in request.files.getlist("slides") if f.filename]

                if len(uploads) > 6:

                    abort(400, "Choose up to six photographs.")

                if uploads:

                    descriptions = request.form.getlist("slide_alt")
                    if not descriptions:
                        descriptions = request.form.get("slide_descriptions", "").splitlines()
                    descriptions = (descriptions + [""] * len(uploads))[:len(uploads)]
                    images = [photograph(f) for f in uploads]

                    slides = '<div class="home-slideshow"><div class="slide-track">' + ''.join(

                        '<img alt="'+html.escape(alt.strip(), quote=True)+'" src="data:image/jpeg;base64,'+image+'">'

                        for image, alt in zip(images, descriptions)) + '</div><button class="slideshow-toggle" type="button">Pause photographs</button></div>'

                    source = re.sub(r'<!-- home slides -->.*?<!-- end home slides -->', '', source, flags=re.S)

                    source = source.replace('<section class="lead home">', '<!-- home slides -->'+slides+'<!-- end home slides --><section class="lead home">')

                if request.form.get("remove_slides"):

                    source = re.sub(r'<!-- home slides -->.*?<!-- end home slides -->', '', source, flags=re.S)

            with NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as temp:

                temp.write(source)

            os.replace(temp.name, path)

            return redirect(url_for("pages", page=name))

        import hashlib

        return render_template("pages.html", names=names, name=name,

            fields=fields, current_photo=current_photo, slide_previews=slide_previews,

            version=hashlib.sha256(source.encode()).hexdigest())

    return app





if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument("command", choices=["setup","serve"], default="serve", nargs="?")

    parser.add_argument("--port", type=int, default=8767, help="Local dashboard port")

    args = parser.parse_args()

    app = create_app()

    if args.command == "setup":

        password = getpass("Set Ashley Mutamiri's founder password (at least 14 characters): ")

        if len(password)<14 or password != getpass("Confirm password: "):

            raise SystemExit("Password too short or confirmation did not match.")

        with closing(connect(app)) as db, db:

            db.executemany("INSERT OR REPLACE INTO settings VALUES (?,?)", [

                ("password",generate_password_hash(password,method="pbkdf2:sha256:600000")),

                ("generation",secrets.token_hex(24))])

            db.execute("DELETE FROM failures")

        print(f"Founder password set. Open http://127.0.0.1:{args.port}/founder/")

    else:

        app.run(host="127.0.0.1",port=args.port,debug=False)



