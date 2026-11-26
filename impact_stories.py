"""Add the supplied sewing and family housing media to the public stories."""

from pathlib import Path
import re


SEWING_MEDIA = '''
<div class="impact-media">
  <div class="impact-grid">
    <img src="/sewing-story-1.jpg" alt="A woman holds up a patterned garment she made" loading="lazy">
    <img src="/sewing-story-2.jpg" alt="A finished blue patterned dress" loading="lazy">
    <img src="/sewing-story-3.jpg" alt="The sewing machine BeHeard Zimbabwe provided" loading="lazy">
  </div>
  <div class="impact-grid impact-videos">
    <figure><video controls playsinline preload="none" poster="/sewing-story-1.jpg" aria-label="Showing her finished sewing work" src="/sewing-finished-work.mp4"></video>
      <figcaption>Showing her finished sewing work</figcaption></figure>
    <figure><video controls playsinline preload="none" poster="/sewing-story-3.jpg" aria-label="Sewing at her machine" src="/sewing-at-machine.mp4"></video>
      <figcaption>Sewing at her machine</figcaption></figure>
    <figure><video controls playsinline preload="none" aria-label="Crushing cans before receiving the sewing machine" src="/crushing-cans.mp4"></video>
      <figcaption>Before receiving the sewing machine, she crushed cans to earn $1.</figcaption></figure>
  </div>
</div>
'''

FAMILY_STORY = '''
<section id="assisting-vulnerable-families" class="block">
  <div class="wrap split"><h2>Assisting Vulnerable Families</h2><div class="prose">
    <p>With the help of well-wishers, we helped a family move from these living conditions into a better home.</p>
    <div class="impact-grid">
      <img src="/family-home-1.jpg" alt="Entrance to the family's previous shelter" loading="lazy">
      <img src="/family-home-2.jpg" alt="Inside the family's previous living quarters" loading="lazy">
      <img src="/family-home-3.jpg" alt="Exterior of the family's previous shelter" loading="lazy">
    </div>
  </div></div>
</section>
'''


def install_impact_stories(public, db):
    key = 'sewing-and-family-stories-v1'
    if db.execute('SELECT 1 FROM settings WHERE key=?', (key,)).fetchone():
        return

    page = Path(public) / 'stories.html'
    source = page.read_text(encoding='utf-8')
    if 'id="sewing-story"' not in source:
        section = re.search(
            r'<section class="[^"]*"><div class="wrap split"><h2>Women and Community Empowerment</h2>'
            r'<div class="prose">.*?</section>', source, re.S,
        )
        if not section:
            raise RuntimeError('Women and Community Empowerment story placement requires review')
        story = section[0].replace('<section ', '<section id="sewing-story" ', 1)
        story = story.removesuffix('</div></div></section>') + SEWING_MEDIA + '</div></div></section>'
        source = source[:section.start()] + story + FAMILY_STORY + source[section.end():]
        page.write_text(source, encoding='utf-8')

    programme = Path(public) / 'programmes.html'
    source = programme.read_text(encoding='utf-8')
    link = '<a class="inline-link" href="/stories.html#sewing-story">Success Stories</a>'
    if link not in source:
        section = re.search(r'<section id="empowerment"[^>]*>.*?</section>', source, re.S)
        if section and section[0].endswith('</div></div></section>'):
            updated = section[0].removesuffix('</div></div></section>') + link + '</div></div></section>'
            programme.write_text(source[:section.start()] + updated + source[section.end():], encoding='utf-8')

    db.execute('INSERT INTO settings VALUES (?,?)', (key, 'installed'))
