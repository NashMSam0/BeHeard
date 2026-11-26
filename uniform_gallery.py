"""One-time installation of the approved uniform story photographs."""
from pathlib import Path

CAPTION = "Providing school uniforms to vulnerable children through the generosity of well-wishers."


def install_uniform_gallery(public, db):
    key = "uniform-gallery-2026-11"
    if db.execute("SELECT 1 FROM settings WHERE key=?", (key,)).fetchone():
        return
    page = Path(public) / "stories.html"
    source = page.read_text(encoding="utf-8")
    anchor = "<p>" + CAPTION + "</p>"
    if source.count(anchor) != 1:
        raise RuntimeError("Uniform story placement requires review")
    if 'class="home-slideshow uniform-gallery"' not in source:
        images = ''.join('<img src="/uniform-' + str(i) + '.jpg" alt="School uniform provided through BeHeard Zimbabwe" width="930" height="1080" loading="lazy">' for i in range(1, 4))
        gallery = '<!-- home slides --><div class="home-slideshow uniform-gallery" role="region" aria-label="School uniform photographs"><div class="slide-track" tabindex="0">' + images + '</div><button class="slideshow-toggle" type="button">Pause photographs</button></div><!-- end home slides -->'
        page.write_text(source.replace(anchor, anchor + gallery, 1), encoding="utf-8")
    db.execute("INSERT INTO settings VALUES (?,?)", (key, "installed"))
