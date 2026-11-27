"""Install the approved founder profile and compact family categories once."""
from pathlib import Path
import re

FOUNDER = '<section id="founder" class="block tinted"><div class="wrap founder-profile"><img src="/ashley-mutamiri.jpg" alt="Ashley Mutamiri, founder of BeHeard Zimbabwe" width="802" height="1080" loading="lazy"><div class="prose"><h2>Meet Our Founder</h2><p>Ashley Mutamiri was born and raised in Victoria Falls. Growing up, she saw firsthand the challenges faced by children and families in vulnerable communities. Those experiences inspired her to found BeHeard Zimbabwe so that people in her hometown would have someone to listen to them and somewhere to turn for support.</p><p>Ashley is a registered social worker with a Bachelor of Science in Social Work and a passion for child protection. An outstanding public speaker, she served as Junior Vice President for Bulawayo Province with Justice for Children in 2018.</p><p>Through BeHeard Zimbabwe, Ashley is working to make psychosocial support more accessible by developing a counselling centre in Victoria Falls. The organisation also helps children stay in school through the Carlos Scholarships, which assist with school fees, uniforms, stationery and other essentials.</p></div></div></section>'

def install_founder_and_family(public, db):
    key = "founder-and-family-categories-v1"
    if db.execute("SELECT 1 FROM settings WHERE key=?", (key,)).fetchone():
        return
    page = Path(public) / "about.html"
    source = page.read_text(encoding="utf-8")
    source, count = re.subn(r'<section id="founder"[^>]*>.*?</section>', lambda m: FOUNDER, source, count=1, flags=re.S)
    if count != 1:
        raise RuntimeError("Founder section missing")
    page.write_text(source, encoding="utf-8")
    page = Path(public) / "stories.html"
    source = page.read_text(encoding="utf-8")
    def compact(match):
        section = match[0]
        marker = '<article id="family-donation"'
        start = section.index('<div class="impact-grid">')
        donation = section.index(marker)
        end = section.index('</article>', donation) + len('</article>')
        housing = section[start:donation]
        gift = section[donation:end]
        categories = ('<div class="education-categories family-categories">'
            '<details name="family-stories"><summary>Family Housing</summary>' + housing + '</details>'
            '<details name="family-stories"><summary>Family Donation</summary>' + gift + '</details></div>')
        return section[:start] + categories + section[end:]
    source, count = re.subn(r'<section id="assisting-vulnerable-families"[^>]*>.*?</section>', compact, source, count=1, flags=re.S)
    if count != 1:
        raise RuntimeError("Family section missing")
    page.write_text(source, encoding="utf-8")
    db.execute("INSERT INTO settings VALUES (?,?)", (key, "installed"))
