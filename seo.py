"""Search metadata applied at delivery, preserving founder-edited HTML."""
import html
import os
import re
from urllib.parse import urlsplit

from flask import Response, redirect, request

PAGES = ("", "about.html", "programmes.html", "stories.html", "involved.html",
         "contact.html", "privacy.html")


def configure_seo(app):
    origin = os.environ.get("BEHEARD_PUBLIC_URL", "https://beheard-zimbabwe.onrender.com").rstrip("/")
    parsed = urlsplit(origin)
    if parsed.scheme != "https" or not parsed.netloc or parsed.path or parsed.query or parsed.fragment or parsed.username:
        raise ValueError("BEHEARD_PUBLIC_URL must be an HTTPS origin without a path")

    @app.get("/index.html")
    def canonical_home():
        return redirect(origin + "/", code=301)

    @app.get("/robots.txt")
    def robots():
        # Let crawlers read the noindex header on the login page.
        return Response("User-agent: *\nAllow: /\nSitemap: " + origin + "/sitemap.xml\n", mimetype="text/plain")

    @app.get("/sitemap.xml")
    def sitemap():
        urls = "".join("<url><loc>" + html.escape(origin + "/" + path) + "</loc></url>" for path in PAGES)
        return Response('<?xml version="1.0" encoding="UTF-8"?>\n'
                        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + urls + '</urlset>', mimetype="application/xml")

    @app.after_request
    def metadata(response):
        if request.path.startswith("/founder") or request.path == "/healthz":
            response.headers["X-Robots-Tag"] = "noindex, nofollow"
        if request.path.lstrip("/") not in PAGES or response.status_code != 200 or response.mimetype != "text/html":
            return response
        response.direct_passthrough = False
        document = response.get_data(as_text=True)
        title = re.search(r"<title>(.*?)</title>", document, re.S | re.I)
        description = re.search(r'<meta\s+name="description"\s+content="([^"]*)"', document, re.I)
        canonical = html.escape(origin + request.path, quote=True)
        # Reuse existing approved wording. Never invent descriptions or claims.
        tags = '\n<link rel="canonical" href="' + canonical + '">\n'
        tags += '<meta property="og:type" content="website">\n<meta property="og:url" content="' + canonical + '">\n'
        tags += '<meta property="og:site_name" content="BeHeard Zimbabwe">\n'
        for key, match in (("title", title), ("description", description)):
            if match:
                value = html.escape(html.unescape(match.group(1)), quote=True)
                tags += '<meta property="og:' + key + '" content="' + value + '">\n'
        document = re.sub(r'<link\b[^>]*rel="canonical"[^>]*>|<meta\b[^>]*property="og:[^"]*"[^>]*>', '', document, flags=re.I)
        response.set_data(document.replace("</head>", tags + "</head>", 1))
        response.headers.pop("ETag", None)
        response.headers.pop("Last-Modified", None)
        response.headers["Cache-Control"] = "no-cache"
        return response
