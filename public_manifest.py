"""Reviewed public file allowlist, shared with the dependency-free static builder."""
import hashlib
import json

PUBLIC_PAGES = ("index.html", "about.html", "programmes.html", "stories.html", "involved.html",
                "contact.html", "privacy.html", "board.html", "gallery.html")
PUBLIC_ASSETS = (
    "styles.css", "site.js", "ashley-mutamiri.jpg", "carlos-birthday-1.jpg", "carlos-birthday-2.jpg", "carlos-birthday-3.jpg", "carlos-birthday-4.jpg", "carlos-birthday-5.jpg", "carlos-birthday-6.jpg", "carlos-birthday-7.jpg", "beheard-logo.jpg", "home-community.jpg",
    "uniform-1.jpg", "uniform-2.jpg", "uniform-3.jpg", "stationary-1.jpg", "stationary-2.jpg",
    "sewing-story-1.jpg", "sewing-story-2.jpg", "sewing-story-3.jpg",
    "family-home-1.jpg", "family-home-2.jpg", "family-home-3.jpg",
    "school-visit.jpg", "family-donation.jpg", "christmas-outreach.jpg", "christmas-programme.jpg",
    "crushing-cans.mp4", "sewing-at-machine.mp4", "sewing-finished-work.mp4",
    "former-home-exterior.mp4", "former-home-room.mp4", "former-home-bathroom.mp4",
)
PUBLIC_FILES = frozenset((*PUBLIC_PAGES, *PUBLIC_ASSETS, "robots.txt", "sitemap.xml"))
MAX_ARTIFACT_BYTES = 128 * 1024 * 1024


def artifact_digest(files):
    manifest = {name: hashlib.sha256(body).hexdigest() for name, body in sorted(files.items())}
    return hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest(), manifest
