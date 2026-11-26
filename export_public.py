"""Offline review export of public files. Does not open or modify private state."""
import argparse
from pathlib import Path

from flask import Flask

from public_artifact import collect_public, pack_artifact
from seo import public_origin


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--public", type=Path, default=Path(__file__).parent / "dist")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    app = Flask(__name__, static_folder=str(args.public.resolve()))
    app.config["PUBLIC_ORIGIN"] = public_origin()
    digest, body = pack_artifact(collect_public(app))
    # Explicit creation only, preventing accidental replacement of another artifact.
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("xb") as output:
        output.write(body)
    print("Exported public review release " + digest)


if __name__ == "__main__":
    main()
