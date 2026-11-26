"""Search metadata applied at delivery, preserving founder-edited HTML."""
import html
import os
import re
from urllib.parse import urlsplit

from flask import Response, redirect, request

PAGES = ("", "about.html", "programmes.html", "stories.html", "involved.html",
         "contact.html", "privacy.html", "board.html", "gallery.html")


def public_origin(value=None):
    origin = (value or os.environ.get("BEHEARD_PUBLIC_URL", "https://beheard-zimbabwe.onrender.com")).rstrip("/")
    parsed = urlsplit(origin)
    if parsed.scheme != "https" or not parsed.netloc or parsed.path or parsed.query or parsed.fragment or parsed.username:
        raise ValueError("BEHEARD_PUBLIC_URL must be an HTTPS origin without a path")
    return origin


def robots_text(origin, staging=False):
    if staging:
        return "User-agent: *\nDisallow: /\n"
    return "User-agent: *\nAllow: /\nSitemap: " + origin + "/sitemap.xml\n"


def sitemap_xml(origin):
    urls = "".join("<url><loc>" + html.escape(origin + "/" + path) + "</loc></url>" for path in PAGES)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + urls + '</urlset>')


def add_metadata(document, path, origin):
    title = re.search(r"<title>(.*?)</title>", document, re.S | re.I)
    description = re.search(r'<meta\s+name="description"\s+content="([^"]*)"', document, re.I)
    canonical = html.escape(origin + path, quote=True)
    tags = '\n<link rel="canonical" href="' + canonical + '">\n'
    tags += '<meta property="og:type" content="website">\n<meta property="og:url" content="' + canonical + '">\n'
    tags += '<meta property="og:site_name" content="BeHeard Zimbabwe">\n'
    for key, match in (("title", title), ("description", description)):
        if match:
            value = html.escape(html.unescape(match.group(1)), quote=True)
            tags += '<meta property="og:' + key + '" content="' + value + '">\n'
    document = re.sub(r'<link\b[^>]*rel="canonical"[^>]*>|<meta\b[^>]*property="og:[^"]*"[^>]*>', '', document, flags=re.I)
    return document.replace("</head>", tags + "</head>", 1)


def configure_seo(app):
    origin = public_origin()
    app.config["PUBLIC_ORIGIN"] = origin

    @app.before_request
    def forward_public_pages():
        if (app.config.get("ADMIN_ONLY") and request.method in ("GET", "HEAD")
                and request.path in {"/" + path for path in PAGES}
                and request.host.lower() != urlsplit(origin).netloc.lower()):
            return redirect(origin + request.path, code=302)

    @app.get("/index.html")
    def canonical_home():
        return redirect(origin + "/", code=301)

    @app.get("/robots.txt")
    def robots():
        # Let crawlers read the noindex header on the login page.
        return Response(robots_text(origin, staging=app.config.get("ADMIN_ONLY", False)), mimetype="text/plain")

    @app.get("/sitemap.xml")
    def sitemap():
        return Response(sitemap_xml(origin), mimetype="application/xml")

    @app.after_request
    def metadata(response):
        if request.path.startswith(("/founder", "/publication")) or request.path == "/healthz" or app.config.get("ADMIN_ONLY"):
            response.headers["X-Robots-Tag"] = "noindex, nofollow"
        if request.path.lstrip("/") not in PAGES or response.status_code != 200 or response.mimetype != "text/html":
            return response
        response.direct_passthrough = False
        response.set_data(add_metadata(response.get_data(as_text=True), request.path, origin))
        response.headers.pop("ETag", None)
        response.headers.pop("Last-Modified", None)
        response.headers["Cache-Control"] = "no-cache"
        return response
