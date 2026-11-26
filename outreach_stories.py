"""Install the family outreach updates and Christmas party announcement."""

from pathlib import Path
import re


FAMILY_MEDIA = '''
<div class="impact-grid">
  <img src="/family-home-1.jpg" alt="Entrance to the family's previous shelter" loading="lazy">
  <img src="/family-home-2.jpg" alt="Inside the family's previous living quarters" loading="lazy">
  <img src="/family-home-3.jpg" alt="Exterior of the family's previous shelter" loading="lazy">
</div>
<div class="impact-grid impact-videos">
  <figure><video controls playsinline preload="none" poster="/family-home-3.jpg" src="/former-home-exterior.mp4" aria-label="Video of the family's former home"></video>
    <figcaption>The family’s former home</figcaption></figure>
  <figure><video controls playsinline preload="none" poster="/family-home-2.jpg" src="/former-home-room.mp4" aria-label="Video of the former sleeping area"></video>
    <figcaption>A mother, her daughter and the grandmother slept on this floor.</figcaption></figure>
  <figure><video controls playsinline preload="none" src="/former-home-bathroom.mp4" aria-label="Video of the former bathroom"></video>
    <figcaption>The bathroom had no toilet. The family used the bush.</figcaption></figure>
</div>
<article id="family-donation" class="family-donation">
  <h3>Family Donation</h3>
  <p>A donation was given to one family, witnessed by a senior teacher from the school.</p>
  <img src="/family-donation.jpg" alt="Food and school supplies presented to a family at the school" width="1080" height="810" loading="lazy">
</article>
'''

CHRISTMAS_EVENT = '''
<article id="childrens-christmas-party" class="news-item christmas-event">
  <time datetime="2026-12-26">26 December 2026</time>
  <h3>Children’s Christmas Party</h3>
  <div class="event-posters">
    <a href="/christmas-outreach.jpg"><img src="/christmas-outreach.jpg" alt="Community Christmas Outreach Initiative and sponsorship poster" loading="lazy"></a>
    <a href="/christmas-programme.jpg"><img src="/christmas-programme.jpg" alt="Children’s Christmas Party programme and timetable" loading="lazy"></a>
  </div>
</article>
'''


def install_outreach_stories(public, db):
    key = 'family-donation-and-christmas-v1'
    if db.execute('SELECT 1 FROM settings WHERE key=?', (key,)).fetchone():
        return
    page = Path(public) / 'stories.html'
    source = page.read_text(encoding='utf-8')
    if 'id="family-donation"' not in source:
        source, count = re.subn(
            r'(<section id="assisting-vulnerable-families"[^>]*>.*?<p>[^<]*</p>)\s*'
            r'<div class="impact-grid">.*?</div>',
            lambda match: match[1] + FAMILY_MEDIA, source, count=1, flags=re.S,
        )
        if count != 1:
            raise RuntimeError('Family outreach story placement requires review')
    if 'id="childrens-christmas-party"' not in source:
        marker = '<!-- published news -->'
        if source.count(marker) != 1:
            raise RuntimeError('Christmas party placement requires review')
        source = source.replace(marker, CHRISTMAS_EVENT + marker, 1)
    page.write_text(source, encoding='utf-8')
    db.execute('INSERT INTO settings VALUES (?,?)', (key, 'installed'))
