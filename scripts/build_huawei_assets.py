"""Extract the Huawei icons the owner accepted for private personal use (D-018).

Each library is checked against its pinned hashes before any entry is read, and it is parsed as
data. An entry is taken only at its pinned index and exact title. SVG bytes are kept as decoded,
and PNG needs rsvg-convert. Rights are not cleared by this script or by the owner's decision.
"""

import argparse
import base64
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "src/cloud_architecture_diagrams/assets/huawei"
MANIFEST = ROOT / "src/cloud_architecture_diagrams/catalog_data/assets.json"
INVENTORY = ROOT / "doc/project-management/evidence/S06-latam-pack-inventory.json"
PACK = "huawei-latam-color"
COMMIT = "52c33aa12fb816a5de403da85067e1c0f039b5be"
PNG_EDGE = 256
# Library path -> (Git blob, SHA-256), both pinned from the audited commit.
SOURCES = {
    "color/HWC Compute and Containers (color).xml": (
        "25f09928318db73046cccc67240df66b5f4f44ab",
        "7db11f19ad3ad95753b8a57ebb0e3b9b17a3d15728b2cee2b4263893e2b00f16",
    ),
    "color/HWC Databases (color).xml": (
        "e122b11e7cb424ade604e84872029dd93aaaac29",
        "dbaa9684c7e2ddf66daea7c56cda0c32be7da2efc75704e4d40e3d1e9d60e08b",
    ),
    "color/HWC Management and Governance (color).xml": (
        "5d4c80d517b8776a57a481529613d05f183c8ff7",
        "45a3d76cad0ff924320b90f748a597b2374b5992bb16c54947a73a898eef80e2",
    ),
    "color/HWC Middleware (color).xml": (
        "f656575ff0321fe6660d8545da14509140190cbc",
        "f9b4397983cb60ca5b083e13dfc198e4642cfc34f6933d7c51e901ed4e5bf32a",
    ),
    "color/HWC Networking (color).xml": (
        "c065b741f88758a986b978946962690508d0dd7c",
        "fb53d316edabdce8a7c211283747b16899734d0b92e17aa474641258170bcbda",
    ),
    "color/HWC Storage (color).xml": (
        "5b2e0af9a4067a3cf87e28593e0fab498f8570e1",
        "22d9927592d46af044485b84103feb5bae2e2d0657ff62d67d96e9ca196d4893",
    ),
}
COMPUTE, DATABASES, MANAGEMENT, MIDDLEWARE, NETWORKING, STORAGE = SOURCES
# Asset ID -> (library, entry index, exact title, required native label).
MAPPING = {
    "huawei-vpc": (NETWORKING, 9, "Virtual Private Cloud (VPC)", "VPC"),
    "huawei-ecs": (COMPUTE, 6, "Elastic Cloud Server (ECS)", "Elastic Cloud Server"),
    "huawei-elb": (NETWORKING, 3, "Elastic Load Balance (ELB)", "Elastic Load Balance"),
    "huawei-eip": (NETWORKING, 2, "Elastic IP (EIP)", "Elastic IP"),
    "huawei-nat": (NETWORKING, 8, "NAT Gateway", "NAT Gateway"),
    "huawei-cce": (COMPUTE, 12, "Cloud Container Engine (CCE)", "CCE"),
    "huawei-rds": (
        DATABASES,
        15,
        "Relational Database Service (RDS)",
        "Relational Database Service",
    ),
    "huawei-obs": (STORAGE, 8, "Object Storage Service (OBS)", "Object Storage Service"),
    "huawei-iam": (
        MANAGEMENT,
        7,
        "Identity and Access Management (IAM)",
        "Identity and Access Management",
    ),
    "huawei-apig": (MIDDLEWARE, 4, "API Gateway (APIG)", "API Gateway"),
    "huawei-functiongraph": (COMPUTE, 8, "FunctionGraph", "FunctionGraph"),
    "huawei-vpn": (NETWORKING, 10, "Virtual Private Network (VPN)", "Virtual Private Network"),
    "huawei-dc": (NETWORKING, 1, "Direct Connect", "Direct Connect"),
    "huawei-ces": (MANAGEMENT, 2, "Cloud Eye Service (CES)", "Cloud Eye"),
    "huawei-lts": (MANAGEMENT, 8, "Log Tank Servce (LTS)", "Log Tank Service"),
    # S16 (D-053): selected P1 coverage. Both DMS editions draw the DMS entry, because the
    # library's "Kafka" and "RabbitMQ" titles do not name Huawei's service.
    "huawei-dcs": (
        MIDDLEWARE,
        7,
        "Distributed Cache Service (DCS) for Redis",
        "Distributed Cache Service",
    ),
    "huawei-dds": (DATABASES, 4, "Document Database Service (DDS)", "Document Database Service"),
    "huawei-gaussdb": (DATABASES, 5, "GaussDB", "GaussDB"),
    "huawei-dms": (
        MIDDLEWARE,
        8,
        "Distributed Message Service (DMS)",
        "Distributed Message Service",
    ),
    "huawei-smn": (
        MANAGEMENT,
        15,
        "Simple Message Notification (SMN)",
        "Simple Message Notification",
    ),
    "huawei-swr": (
        COMPUTE,
        15,
        "SoftWare Repository for Container (SWR)",
        "SoftWare Repository for Container",
    ),
    "huawei-cci": (COMPUTE, 13, "Cloud Container Instance (CCI)", "Cloud Container Instance"),
    "huawei-sfs": (STORAGE, 9, "Scalable File Service (SFS)", "Scalable File Service"),
    "huawei-sfs-turbo": (STORAGE, 10, "Scalable File Service (SFS) Turbo", "SFS Turbo"),
    "huawei-evs": (STORAGE, 6, "Elastic Volume Service (EVS)", "Elastic Volume Service"),
    "huawei-cbr": (STORAGE, 0, "Cloud Backup and Recovery (CBR)", "Cloud Backup and Recovery"),
    "huawei-er": (NETWORKING, 5, "Enterprise Router (ER)", "Enterprise Router"),
    "huawei-vpcep": (NETWORKING, 11, "VPC Endpoint (VPCEP)", "VPC Endpoint"),
    "huawei-ga": (NETWORKING, 7, "Global Accelerator (GA)", "Global Accelerator"),
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(data) + data, usedforsecurity=False).hexdigest()


def library(root: Path, path: str) -> list[dict[str, str]]:
    raw = (root / path).read_bytes()
    blob, sha256 = SOURCES[path]
    if git_blob(raw) != blob or digest(raw) != sha256:
        raise SystemExit(f"{path} differs from the pinned file; review it before changing the pin")
    match = re.fullmatch(r"\s*<mxlibrary>(.*)</mxlibrary>\s*", raw.decode(), re.DOTALL)
    assert match, path
    entries: list[dict[str, str]] = json.loads(match.group(1))
    return entries


def decoded(entry: dict[str, str]) -> bytes:
    found = re.fullmatch(r"data:image/svg\+xml;base64,(.*)", entry["data"], re.DOTALL)
    assert found, entry["title"]
    return base64.b64decode(found.group(1), validate=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path, help="Directory holding the pinned color libraries")
    args = parser.parse_args()
    libraries = {path: library(args.root, path) for path in SOURCES}
    ASSETS.mkdir(parents=True, exist_ok=True)
    for stale in [*ASSETS.glob("*.png"), *ASSETS.glob("*.svg")]:
        stale.unlink()
    records: list[dict[str, object]] = []
    for asset_id, (path, index, title, label) in MAPPING.items():
        entry = libraries[path][index]
        assert entry["title"] == title, (asset_id, entry["title"])
        svg = decoded(entry)
        base = asset_id.removeprefix("huawei-")
        (ASSETS / f"{base}.svg").write_bytes(svg)
        subprocess.run(
            [
                "rsvg-convert",
                "-w",
                str(PNG_EDGE),
                "-h",
                str(PNG_EDGE),
                "-o",
                ASSETS / f"{base}.png",
                ASSETS / f"{base}.svg",
            ],
            check=True,
        )
        records.append(
            {
                "id": asset_id,
                "pack": PACK,
                "concept": label,
                "required_label": label,
                "composition": "direct",
                "symbols": [title],
                "original": [
                    {
                        "name": title,
                        "sha256": digest(svg),
                        "digest_of": "decoded_svg",
                        "entry_index": index,
                        "source_path": path,
                    }
                ],
                "derived": {
                    "svg": {"path": f"assets/huawei/{base}.svg", "sha256": digest(svg)},
                    "png": {
                        "path": f"assets/huawei/{base}.png",
                        "sha256": digest((ASSETS / f"{base}.png").read_bytes()),
                        "width": PNG_EDGE,
                        "height": PNG_EDGE,
                    },
                },
                "changes": "The SVG is unchanged from the decoded entry; the PNG is rasterized from it",
            }
        )
    manifest = json.loads(MANIFEST.read_text())
    kept = [item for item in manifest["assets"] if not item["pack"].startswith("huawei-")]
    manifest["assets"] = kept + records
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=True) + "\n")
    INVENTORY.write_text(
        json.dumps(
            {
                "repository": "https://github.com/huaweicloud-latam/drawio-libraries",
                "commit": COMMIT,
                "note": "Metadata only; this file holds no artwork. Listing an entry maps nothing.",
                "files": [
                    {"path": path, "git_blob": blob, "sha256": sha256}
                    for path, (blob, sha256) in SOURCES.items()
                ],
                "entries": [
                    {
                        "file": path,
                        "index": index,
                        "title": entry["title"],
                        "bytes": len(decoded(entry)),
                        "sha256": digest(decoded(entry)),
                    }
                    for path, entries in libraries.items()
                    for index, entry in enumerate(entries)
                ],
            },
            indent=1,
        )
        + "\n"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
