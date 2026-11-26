"""Persist the single-instance editor state outside Render's ephemeral filesystem."""
import base64
import json
import os
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
from urllib.request import Request, urlopen


class CloudState:
    def __init__(self, private, public):
        self.private = Path(private)
        self.public = Path(public)
        self.url = os.environ["BEHEARD_STATE_URL"].rstrip("/") + "/rest/v1/beheard_state"
        self.key = os.environ["BEHEARD_STATE_API_KEY"]
        self.token = os.environ["BEHEARD_STATE_TOKEN"]
        self.revision = 0

    def request(self, method="GET", query="", data=None):
        headers = {"apikey": self.key, "x-beheard-key": self.token,
                   "Content-Type": "application/json", "Prefer": "return=representation"}
        body = json.dumps(data).encode() if data is not None else None
        with urlopen(Request(self.url + query, data=body, headers=headers, method=method), timeout=25) as result:
            return json.load(result)

    def restore(self):
        rows = self.request(query="?id=eq.1&select=revision,payload")
        if len(rows) != 1:
            raise RuntimeError("Website storage access unavailable")
        row = rows[0]
        self.revision = row["revision"]
        if row["payload"] is None:
            return
        payload = row["payload"]
        database = base64.b64decode(payload["database"], validate=True)
        temp = self.private / "restore.tmp"
        temp.write_bytes(database)
        os.replace(temp, self.private / "publisher.sqlite3")
        for name, content in payload["pages"].items():
            if Path(name).name != name or not name.endswith(".html"):
                raise ValueError("Invalid saved page")
            target = self.public / name
            temp_page = target.with_suffix(".tmp")
            temp_page.write_text(content, encoding="utf-8")
            os.replace(temp_page, target)

    def save(self):
        # Use SQLite backup so a snapshot always contains a consistent database.
        with TemporaryDirectory() as tmp:
            backup = Path(tmp) / "state.sqlite3"
            with sqlite3.connect(self.private / "publisher.sqlite3") as source:
                with sqlite3.connect(backup) as destination:
                    source.backup(destination)
            database = base64.b64encode(backup.read_bytes()).decode("ascii")
        pages = {p.name: p.read_text("utf-8") for p in self.public.glob("*.html")}
        revision = self.revision + 1
        rows = self.request("PATCH", "?id=eq.1&revision=eq." + str(self.revision),
                            {"revision": revision, "payload": {"database": database, "pages": pages}})
        if len(rows) != 1:
            raise RuntimeError("Website content changed on another instance")
        self.revision = revision
