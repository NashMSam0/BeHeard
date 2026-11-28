import re
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
from publisher import create_app, connect

class SubmissionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        shutil.copytree(Path(__file__).resolve().parents[1] / "dist", root / "public")
        self.app = create_app(root / "private", root / "public")
        self.client = self.app.test_client()

    def tearDown(self):
        self.temp.cleanup()

    def test_consent_and_private_inbox(self):
        response = self.client.get("/forms/counselling")
        token = re.search(rb'name="token" value="([^"]+)"', response.data)[1].decode()
        data = dict(token=token, name="Test person", email="test@example.org", phone="", message="Monday morning")
        self.assertEqual(self.client.post("/forms/counselling", data=data).status_code, 400)
        data["consent"] = "yes"
        response = self.client.post("/forms/counselling", data=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"has been saved", response.data)
        db = connect(self.app)
        row = db.execute("SELECT * FROM submissions").fetchone()
        self.assertEqual(row["kind"], "counselling")
        self.assertTrue(row["consent"])
        self.assertEqual(row["notified"], 0)
        db.close()
        self.assertEqual(self.client.get("/admindashboard/submissions").status_code, 302)
        self.assertEqual(response.headers["Cache-Control"], "no-store")

    def test_render_https_origin_behind_proxy(self):
        response = self.client.get("/forms/enquiry")
        token = re.search(rb'name="token" value="([^"]+)"', response.data)[1].decode()
        data = dict(token=token, name="Browser test", email="test@example.org", consent="yes")
        with patch.dict("os.environ", {"RENDER_EXTERNAL_HOSTNAME": "localhost"}):
            response = self.client.post("/forms/enquiry", data=data, headers={"Origin": "https://localhost"})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(self.client.post("/forms/enquiry", data=data,
                headers={"Origin": "https://untrusted.example"}).status_code, 403)

    def test_invalid_token_rejected(self):
        self.assertEqual(self.client.post("/forms/enquiry", data={"token": "bad"}).status_code, 403)

if __name__ == "__main__":
    unittest.main()
