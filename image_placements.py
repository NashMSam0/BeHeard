"""Explicit saved-page section destinations for editor photographs."""
import html
import re

def sections(source):
    result = []
    for index, match in enumerate(re.finditer(r"<section\b[^>]*>.*?</section>", source, re.S)):
        heading = re.search(r"<h[123][^>]*>(.*?)</h[123]>", match[0], re.S)
        if heading:
            label = html.unescape(re.sub(r"<[^>]+>", "", heading[1])).strip()
            result.append((str(index), label, match))
    return result

def place_photo(source, target, photo, alt):
    selected = next((item for item in sections(source) if item[0] == target), None)
    if not selected:
        raise ValueError("Choose a section for this photograph.")
    key, label, match = selected
    block = re.sub(r'<figure class="section-photo"[^>]*>.*?</figure>', "", match[0], flags=re.S)
    image = '<figure class="section-photo"><img src="data:image/jpeg;base64,' + photo + '" alt="' + html.escape(alt, quote=True) + '"></figure>'
    block = block.replace("</section>", image + "</section>", 1)
    return source[:match.start()] + block + source[match.end():]
