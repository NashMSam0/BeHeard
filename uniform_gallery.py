"""One-time installation of the approved uniform story photographs."""
from pathlib import Path
import re

CAPTION = "Providing school uniforms to vulnerable children through the generosity of well-wishers."
APPROVED_CAPTION = "Children wearing uniforms which we provided"
UNIFORM_DESCRIPTION = CAPTION.removesuffix(".")


def install_stationary_photos(public, db):
    key = "stationary-story-photos-v1"
    if db.execute("SELECT 1 FROM settings WHERE key=?", (key,)).fetchone():
        return
    page = Path(public) / "stories.html"
    source = page.read_text(encoding="utf-8")
    anchor = '<summary>Stationary</summary>'
    if source.count(anchor) != 1:
        raise RuntimeError("Stationary story placement requires review")
    gallery = (
        '<div class="home-slideshow uniform-gallery" role="region" aria-label="Stationary photographs">'
        '<div class="slide-track" tabindex="0">'
        '<img src="/stationary-1.jpg" alt="School supplies and shoes laid out on a mat" width="810" height="1080" loading="lazy">'
        '<img src="/stationary-2.jpg" alt="School supplies being sorted outdoors" width="810" height="1080" loading="lazy">'
        '</div></div>'
    )
    if '/stationary-1.jpg' not in source:
        page.write_text(source.replace(anchor, anchor + gallery, 1), encoding="utf-8")
    db.execute("INSERT INTO settings VALUES (?,?)", (key, "installed"))


def install_education_categories(public, db):
    key = "education-story-categories-v1"
    if db.execute("SELECT 1 FROM settings WHERE key=?", (key,)).fetchone():
        return
    page = Path(public) / "stories.html"
    source = page.read_text(encoding="utf-8")
    if 'class="education-categories"' not in source:
        match = re.search(
            r'(<h2>Educational Support</h2>\s*<div class="prose">)\s*<p>[^<]*</p>'
            r'(\s*<!-- home slides -->.*?<!-- end home slides -->)?', source, re.S,
        )
        if not match:
            raise RuntimeError("Educational Support story placement requires review")
        categories = (
            '<div class="education-categories">'
            '<details name="education-stories"><summary>Uniforms</summary>'
            '<ul class="education-story-description"><li><p>' + UNIFORM_DESCRIPTION + '</p></li></ul>'
            + (match[2] or '') + '<!-- end uniforms --></details>'
            '<details name="education-stories"><summary>Stationary</summary></details>'
            '</div>'
        )
        page.write_text(source[:match.start()] + match[1] + categories + source[match.end():], encoding="utf-8")
    db.execute("INSERT INTO settings VALUES (?,?)", (key, "installed"))


def update_uniform_caption(public, db):
    key = "uniform-caption-2026-11"
    if db.execute("SELECT 1 FROM settings WHERE key=?", (key,)).fetchone():
        return
    page = Path(public) / "stories.html"
    source = page.read_text(encoding="utf-8")
    updated = re.sub(
        r'(<h2>Educational Support</h2>\s*<div class="prose">\s*<p>)[^<]*(</p>)',
        lambda match: match[1] + APPROVED_CAPTION + match[2],
        source, count=1,
    )
    if updated != source:
        page.write_text(updated, encoding="utf-8")
    if APPROVED_CAPTION in updated:
        db.execute("INSERT INTO settings VALUES (?,?)", (key, "installed"))


def install_uniform_gallery(public, db):
    key = "uniform-gallery-2026-11"
    if db.execute("SELECT 1 FROM settings WHERE key=?", (key,)).fetchone():
        return
    page = Path(public) / "stories.html"
    source = page.read_text(encoding="utf-8")
    if 'class="education-categories"' in source:
        db.execute("INSERT INTO settings VALUES (?,?)", (key, "installed"))
        return
    anchor = "<p>" + CAPTION + "</p>"
    if anchor not in source:
        anchor = "<p>" + APPROVED_CAPTION + "</p>"
    if source.count(anchor) != 1:
        raise RuntimeError("Uniform story placement requires review")
    if 'class="home-slideshow uniform-gallery"' not in source:
        images = ''.join('<img src="/uniform-' + str(i) + '.jpg" alt="School uniform provided through BeHeard Zimbabwe" width="930" height="1080" loading="lazy">' for i in range(1, 4))
        gallery = '<!-- home slides --><div class="home-slideshow uniform-gallery" role="region" aria-label="School uniform photographs"><div class="slide-track" tabindex="0">' + images + '</div><button class="slideshow-toggle" type="button">Pause photographs</button></div><!-- end home slides -->'
        page.write_text(source.replace(anchor, anchor + gallery, 1), encoding="utf-8")
    db.execute("INSERT INTO settings VALUES (?,?)", (key, "installed"))
