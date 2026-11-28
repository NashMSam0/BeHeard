"""Shared public rendering for Flask and the static publisher."""
from pathlib import Path
import re

from flask import render_template


def _render_public(public, name):
    public = Path(public)
    document = (public / name).read_text(encoding="utf-8")
    document = document.replace("</head>", '<link rel="icon" href="/favicon.ico" sizes="any"><link rel="apple-touch-icon" href="/apple-touch-icon.png"></head>', 1)
    if name in ("contact.html", "involved.html", "programmes.html"):
        document = document.replace("</main>", render_template("form_links.html", page=name) + "</main>", 1)
    from donations import render_donations
    document = document.replace("</body>", render_donations() + "\n</body>", 1)
    if name == "privacy.html":
        return document.replace("</main>", render_template("privacy_details.html") + "\n</main>", 1)
    if name == "gallery.html":
        from gallery_categories import CATEGORIES
        import html
        uploads = {key: [] for key in CATEGORIES}
        pattern = r'<figure data-gallery-category="([^"]+)"><img alt="([^"]*)" src="([^"]+)"></figure>'
        for match in re.finditer(pattern, document):
            if match[1] in uploads and match[3].startswith("data:image/jpeg;base64,"):
                uploads[match[1]].append((html.unescape(match[3]), html.unescape(match[2])))
        document = re.sub(pattern, "", document)
        if uploads["stationery"]:
            photos = "".join('<a href="' + src + '"><img src="' + src + '" alt="' + html.escape(alt, quote=True) + '" loading="lazy"></a>' for src, alt in uploads["stationery"])
            document, count = re.subn(r'(<h2>Stationary</h2>\s*<div class="gallery-grid">.*?)(</div>)',
                lambda match: match[1] + photos + match[2], document, count=1, flags=re.S)
            if count:
                uploads["stationery"] = []

        return document.replace('</main>', render_template('gallery_groups.html', uploads=uploads) + '\n</main>', 1)
    if name != "index.html":
        return document
    document = re.sub(r'<!-- home slides -->.*?<!-- end home slides -->|<figure class="page-photo">.*?</figure>',
                      '', document, flags=re.S)
    slideshow = ('<section class="home-slideshow" aria-label="BeHeard photographs" data-interval="1500">'
                 '<div class="slide-track"><img src="/home-family-support.jpg" alt="Ashley with children" fetchpriority="high">'
                 '<img src="/home-education-support.jpg" alt="Children with school supplies"></div>'
                 '<button type="button" class="slideshow-toggle">Pause photographs</button></section>')
    document = document.replace('<main id="main" tabindex="-1">', '<main id="main" tabindex="-1">' + slideshow, 1)
    stories = (public / "stories.html").read_text(encoding="utf-8")
    heading = stories.find('<h2 id="news">')
    if heading == -1:
        return document
    start = stories.rfind('<section ', 0, heading)
    end = stories.find('</section>', heading)
    if start == -1 or end == -1:
        return document
    news = stories[start:end + len('</section>')]
    shortcut = '<a class="home-news-shortcut" href="#news">News and Events <span aria-hidden="true">↓</span></a>'
    return document.replace('</main>', news + '\n</main>\n' + shortcut, 1)

def render_public(public, name):
    import hashlib
    import html
    document = _render_public(public, name)
    hidden = set(re.findall(r"<!-- hidden-photo:([a-f0-9]{64}) -->", document))
    def keep_image(match):
        image = re.search(r'<img\b[^>]*src="([^"]+)"', match[0])
        if image and hashlib.sha256(html.unescape(image[1]).encode()).hexdigest() in hidden:
            return ""
        return match[0]
    document = re.sub(r'<a\b[^>]*>\s*<img\b[^>]*>\s*</a>|<img\b[^>]*>', keep_image, document)
    document = re.sub(r'<figure\b[^>]*>\s*</figure>', "", document)
    return re.sub(r"<!-- hidden-photo:[a-f0-9]{64} -->", "", document)
