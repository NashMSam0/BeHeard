"""Shared public rendering for Flask and the static publisher."""
from pathlib import Path
import re

from flask import render_template


def render_public(public, name):
    public = Path(public)
    document = (public / name).read_text(encoding="utf-8")
    if name == "involved.html":
        from donations import render_donations
        return document.replace('</main>', render_donations() + "\n</main>", 1)
    if name == "gallery.html":
        return document.replace('</main>', render_template('gallery_groups.html') + '\n</main>', 1)
    if name != "index.html":
        return document
    document = re.sub(r'<!-- home slides -->.*?<!-- end home slides -->|<figure class="page-photo">.*?</figure>',
                      '', document, flags=re.S)
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
