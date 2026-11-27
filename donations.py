"""Public receiving details only. Never store payment credentials here."""
import json
from pathlib import Path
from urllib.parse import urlsplit

from flask import render_template

SETTINGS = Path(__file__).with_name("donation_settings.json")


def render_donations():
    settings = json.loads(SETTINGS.read_text(encoding="utf-8"))
    bank = settings.get("bank", {})
    ecocash = settings.get("ecocash", {})
    paypal = settings.get("paypal", {})
    for key in ("once_off_url", "monthly_url"):
        url = paypal.get(key, "")
        if url:
            parsed = urlsplit(url)
            if (parsed.scheme != "https" or parsed.hostname not in
                    ("www.paypal.com", "paypal.com", "www.paypal.me", "paypal.me")
                    or parsed.username or parsed.password or parsed.fragment):
                raise ValueError("Configure an official HTTPS PayPal donation link")
    return render_template("donations.html", bank=bank, ecocash=ecocash, paypal=paypal)
