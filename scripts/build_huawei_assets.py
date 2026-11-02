"""Extract the Huawei icons the owner accepted for private personal use (D-017).

Bytes are kept exactly as decoded. The pack is checked against its pinned hashes before any entry
is read, and it is parsed as data. Only titles naming the service are mapped; the rest stay
unmapped rather than guessed, so the repository holds no pack file and no unmapped image.
"""

import argparse
import base64
import hashlib
import json
import re
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "src/cloud_architecture_diagrams/assets/huawei"
MANIFEST = ROOT / "src/cloud_architecture_diagrams/catalog_data/assets.json"
INVENTORY = ROOT / "doc/project-management/evidence/S06-huawei-pack-inventory.json"
PACK = "huawei-juandiaz00-png"
COMMIT = "ea52d7356e172a85cde7538f293a663eb137611d"
SOURCE_PATH = "HuaweiCloud Icons.xml"
GIT_BLOB = "0bd260648d2525e86c87c671ea9f9deb8d825a14"
SOURCE_SHA256 = "1afc1f2a0fda735c7b9eda88466725b720045493e61a04d392467596b8c976cd"
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
# Asset ID -> (source title, title token naming the service, required native label).
MAPPING = {
    "huawei-vpc": ("network-vpc", "vpc", "VPC"),
    "huawei-ecs": ("computing-ecs", "ecs", "Elastic Cloud Server"),
    "huawei-elb": ("network-elb", "elb", "Elastic Load Balance"),
    "huawei-eip": ("network-eip", "eip", "Elastic IP"),
    "huawei-rds": ("database-rds", "rds", "Relational Database Service"),
    "huawei-iam": ("managementdeployment-iam", "iam", "Identity and Access Management"),
    "huawei-vpn": ("network-vpn-2", "vpn", "Virtual Private Network"),
    "huawei-functiongraph": ("computing-fgs", "fgs", "FunctionGraph"),
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(data) + data, usedforsecurity=False).hexdigest()


def entries(source: Path) -> list[dict[str, object]]:
    raw = source.read_bytes()
    if digest(raw) != SOURCE_SHA256 or git_blob(raw) != GIT_BLOB:
        raise SystemExit("The pack differs from the pinned file; review it before changing the pin")
    match = re.fullmatch(r"\s*<mxlibrary>(.*)</mxlibrary>\s*", raw.decode(), re.DOTALL)
    assert match
    rows: list[dict[str, object]] = []
    for index, entry in enumerate(json.loads(match.group(1))):
        found = re.fullmatch(r"data:image/png;base64,(.*)", entry["data"], re.DOTALL)
        assert found, entry["title"]
        png = base64.b64decode(found.group(1), validate=True)
        assert png[:8] == PNG_SIGNATURE
        width, height = struct.unpack(">II", png[16:24])
        rows.append(
            {
                "index": index,
                "title": entry["title"],
                "width": width,
                "height": height,
                "bytes": len(png),
                "sha256": digest(png),
                "png": png,
            }
        )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    args = parser.parse_args()
    rows = entries(args.source)
    by_title = {row["title"]: row for row in rows}
    ASSETS.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, object]] = []
    for asset_id, (title, token, label) in MAPPING.items():
        row = by_title[title]
        png = row["png"]
        assert isinstance(png, bytes)
        relative = f"assets/huawei/{asset_id.removeprefix('huawei-')}.png"
        (ASSETS.parent.parent / relative).write_bytes(png)
        records.append(
            {
                "id": asset_id,
                "pack": PACK,
                "concept": label,
                "required_label": label,
                "composition": "direct",
                "symbols": [title],
                "title_token": token,
                "original": [
                    {
                        "name": title,
                        "sha256": row["sha256"],
                        "digest_of": "decoded_png",
                        "entry_index": row["index"],
                    }
                ],
                "derived": {
                    "svg": None,
                    "png": {
                        "path": relative,
                        "sha256": row["sha256"],
                        "width": row["width"],
                        "height": row["height"],
                    },
                },
                "changes": "None; the decoded PNG bytes are kept unchanged",
            }
        )
    manifest = json.loads(MANIFEST.read_text())
    kept = [item for item in manifest["assets"] if item["pack"] != PACK]
    manifest["assets"] = kept + records
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=True) + "\n")
    INVENTORY.write_text(
        json.dumps(
            {
                "repository": "https://github.com/JuanDiaz00/Huawei-Cloud-draw.io-icons",
                "commit": COMMIT,
                "source_path": SOURCE_PATH,
                "git_blob": GIT_BLOB,
                "source_sha256": SOURCE_SHA256,
                "format": "image/png, 8-bit RGBA, black on transparent, inside a draw.io mxlibrary",
                "note": "Metadata only; this file holds no artwork. Listing an entry maps nothing.",
                "entries": [
                    {key: value for key, value in row.items() if key != "png"} for row in rows
                ],
            },
            indent=1,
        )
        + "\n"
    )
    subprocess.run(["git", "status", "--short", "--", str(ASSETS)], check=True, cwd=ROOT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
