"""Install the Christmas party announcement."""

from pathlib import Path


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


def install_christmas_event(public, db):
    key = 'christmas-party-v1'
    if db.execute('SELECT 1 FROM settings WHERE key=?', (key,)).fetchone():
        return
    page = Path(public) / 'stories.html'
    source = page.read_text(encoding='utf-8')
    if 'id="childrens-christmas-party"' not in source:
        marker = '<!-- published news -->'
        if source.count(marker) != 1:
            raise RuntimeError('Christmas party placement requires review')
        source = source.replace(marker, CHRISTMAS_EVENT + marker, 1)
    page.write_text(source, encoding='utf-8')
    db.execute('INSERT INTO settings VALUES (?,?)', (key, 'installed'))
