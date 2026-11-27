"""Install the supplied scholarship birthday photographs."""
from pathlib import Path
import re

BIRTHDAYS = '<article id="scholarship-birthdays"><h3>Birthday Celebrations</h3><p>We celebrate every child’s birthday under the Carlos Scholarships.</p><div class="home-slideshow uniform-gallery" role="region" aria-label="Carlos Scholarships birthday celebrations"><div class="slide-track" tabindex="0"><img src="/carlos-birthday-1.jpg" alt="Children celebrating a birthday together" loading="lazy"><img src="/carlos-birthday-2.jpg" alt="A child beside a birthday cake and gifts" loading="lazy"><img src="/carlos-birthday-3.jpg" alt="Children gathered around the birthday cake and gifts" loading="lazy"><img src="/carlos-birthday-4.jpg" alt="A decorated birthday cake" loading="lazy"></div></div></article>'

def install_birthdays(public, db):
    key = "carlos-birthdays-v1"
    if db.execute("SELECT 1 FROM settings WHERE key=?", (key,)).fetchone():
        return
    page = Path(public) / "stories.html"
    source = page.read_text(encoding="utf-8")
    pattern = r'(<h2>Carlos.*?Scholarships</h2><div class="prose">.*?)(</div></div></section>)'
    source, count = re.subn(pattern, lambda m: m[1] + BIRTHDAYS + m[2], source, count=1, flags=re.S)
    if count != 1:
        raise RuntimeError("Scholarship section missing")
    page.write_text(source, encoding="utf-8")
    db.execute("INSERT INTO settings VALUES (?,?)", (key, "installed"))
