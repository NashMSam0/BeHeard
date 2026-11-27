"""Link programme sections to the published related stories."""
from pathlib import Path
import re

def install_programme_story_links(public, db):
    key = "programme-story-links-v1"
    if db.execute("SELECT 1 FROM settings WHERE key=?", (key,)).fetchone():
        return
    page = Path(public) / "programmes.html"
    source = page.read_text(encoding="utf-8")
    destinations = {
        "education": "educational-support",
        "empowerment": "sewing-story",
        "child-protection": "scholarship-birthdays",
        "outreach": "assisting-vulnerable-families",
    }
    for section, destination in destinations.items():
        pattern = r'(<section id="' + section + r'"[^>]*>.*?)(</div></div></section>)'
        def add_link(match):
            content = re.sub(r'<a class="inline-link" href="/stories.html[^"]*">Success Stories</a>', "", match[1])
            return content + '<a class="inline-link" href="/stories.html#' + destination + '">Success Stories</a>' + match[2]
        source, count = re.subn(pattern, add_link, source, count=1, flags=re.S)
        if count != 1:
            raise RuntimeError("Programme section missing")
    page.write_text(source, encoding="utf-8")
    db.execute("INSERT INTO settings VALUES (?,?)", (key, "installed"))
