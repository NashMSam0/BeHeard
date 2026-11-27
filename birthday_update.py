"""Add the second supplied birthday celebration once."""
from pathlib import Path
import re

def install_birthday_update(public, db):
    key = "second-birthday-v1"
    if db.execute("SELECT 1 FROM settings WHERE key=?", (key,)).fetchone():
        return
    page = Path(public) / "stories.html"
    source = page.read_text(encoding="utf-8")
    source, count = re.subn(r'(<article id="scholarship-birthdays".*?)(</div></div></article>)', lambda m: m[1] + '<img src="/carlos-birthday-5.jpg" alt="Children together with a birthday cake" loading="lazy"><img src="/carlos-birthday-6.jpg" alt="A scholarship birthday celebration" loading="lazy"><img src="/carlos-birthday-7.jpg" alt="A decorated birthday cake" loading="lazy">' + m[2], source, count=1, flags=re.S)
    if count != 1:
        raise RuntimeError("Birthday gallery missing")
    page.write_text(source, encoding="utf-8")
    db.execute("INSERT INTO settings VALUES (?,?)", (key, "installed"))

def install_third_birthday(public, db):
    key = "third-birthday-v1"
    if db.execute("SELECT 1 FROM settings WHERE key=?", (key,)).fetchone():
        return
    page = Path(public) / "stories.html"
    source = page.read_text(encoding="utf-8")
    source, count = re.subn(r'(<article id="scholarship-birthdays".*?)(</div></div></article>)', lambda m: m[1] + '<img src="/carlos-birthday-8.jpg" alt="A pink birthday cake with butterfly decorations" loading="lazy"><img src="/carlos-birthday-9.jpg" alt="Birthday celebration table and balloon display" loading="lazy"><img src="/carlos-birthday-10.jpg" alt="Pink balloon display and birthday chair" loading="lazy">' + m[2], source, count=1, flags=re.S)
    if count != 1:
        raise RuntimeError("Birthday gallery missing")
    page.write_text(source, encoding="utf-8")
    db.execute("INSERT INTO settings VALUES (?,?)", (key, "installed"))
