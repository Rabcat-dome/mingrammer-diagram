"""M2-05 catalog, inventory and license gate. Missing rights, assets or mappings fail the lane."""

import hashlib
import importlib
import json
import os
import re
import sys
import tomllib
import xml.etree.ElementTree as ET
from collections.abc import Mapping
from importlib.metadata import version
from pathlib import Path
from typing import get_args

from build_native_icon_lock import locate
from build_onprem_assets import CONCEPTS, SHAPES, compose, load_shapes, shape_digest
from build_third_party import runtime_packages
from repository_checks import anchors

from cloud_architecture_diagrams.catalog import (
    DATA,
    AssetManifest,
    Catalog,
    CatalogRecord,
    Pack,
    ProviderFile,
    catalog,
)
from cloud_architecture_diagrams.models import CLUSTER_SCOPED, KubernetesKind

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "src/cloud_architecture_diagrams"
ASSET_SUFFIXES = {
    ".svg", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".bmp", ".tif", ".tiff",
    ".drawio", ".vsdx", ".vssx", ".xml", ".pdf", ".ttf", ".otf", ".woff", ".woff2",
}  # fmt: skip
SVG_ELEMENTS = {"svg", "g", "path", "rect", "ellipse", "defs", "clipPath", "desc"}
SVG_ATTRIBUTES = {
    "xmlns", "viewBox", "width", "height", "transform", "d", "x", "y", "rx", "ry", "cx", "cy",
    "fill", "stroke", "stroke-width", "stroke-dasharray", "id", "clip-path", "fill-rule",
    "fill-opacity",
}  # fmt: skip
DOCUMENTS = {
    "requirements": "doc/requirements/requirements.md",
    "decisions": "doc/project-management/decisions.md",
    "s02-additional": "doc/project-management/evidence/S02-additional-icon-sources.md",
}
REQUIRED_FONTS = {"Noto Sans", "Noto Sans Thai"}
REQUIRED_CONCEPTS = {
    "Load balancer", "Hypervisor", "VM", "NAS", "SAN", "Identity service", "Backup system",
    "Monitoring",
}  # fmt: skip
SOURCE_CHECKS = "doc/project-management/evidence/S06-source-checks.json"
PACK_INVENTORY = "doc/project-management/evidence/S06-latam-pack-inventory.json"
PRIVATE_CLASSIFIER = "Private :: Do Not Upload"
PRIVATE_PHRASE = "private personal use"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def requirement_items(text: str) -> dict[str, list[str]]:
    section = text.split("## 6. Minimum release catalog", 1)[1].split("### 6.1", 1)[0]
    rows = {
        "AWS": "aws",
        "Azure": "azure",
        "GCP": "gcp",
        "Huawei Cloud": "huawei",
        "On-premises": "onprem",
    }
    found: dict[str, list[str]] = {}
    for name, key in rows.items():
        match = re.search(rf"^\| {re.escape(name)} \| (.*?) \|$", section, re.MULTILINE)
        assert match, name
        found[key] = [item.strip() for item in re.split(r"[,;]", match.group(1)) if item.strip()]
    return found


def check_records(data: Catalog, errors: list[str]) -> None:
    seen: set[str] = set()
    for name, file in data.files.items():
        if file.catalog_version != data.version:
            errors.append(f"{name}: catalog_version differs from the taxonomy file")
        for record in file.records:
            if record.id in seen:
                errors.append(f"{record.id}: duplicate type ID")
            seen.add(record.id)
    for record in data.records.values():
        if record.taxonomy not in data.taxonomy_ids:
            errors.append(f"{record.id}: unknown taxonomy {record.taxonomy}")
        if (record.entity == "resource") == (record.kind is not None):
            errors.append(f"{record.id}: kind applies to scopes and boundaries only")
        for source in record.sources:
            check_source(source, record.id, errors)
        if record.id.startswith("k8s.") and "kubernetes" in str(record.providers):
            errors.append(f"{record.id}: Kubernetes must not be a provider")
        check_representation(record, data, errors)
    kinds = {
        record.kubernetes_kinds[0]: record
        for record in data.files["kubernetes"].records
        if record.kubernetes_kinds
    }
    if set(kinds) != set(get_args(KubernetesKind)):
        errors.append("kubernetes: the catalog and the contract list different kinds")
    for kind, record in kinds.items():
        if kind != "IngressController" and bool(record.namespaced) == (kind in CLUSTER_SCOPED):
            errors.append(f"{record.id}: namespaced flag contradicts the core contract")
    for cluster, mode in data.cluster_modes.items():
        if cluster not in data.records or "Cluster" not in data.records[cluster].kubernetes_kinds:
            errors.append(f"{cluster}: cluster mode names no cluster type")
        for pool in mode.node_pool_types:
            if pool not in data.records or "NodePool" not in data.records[pool].kubernetes_kinds:
                errors.append(f"{cluster}: {pool} is not a node-pool type")
    typed_clusters = {r.id for r in data.records.values() if "Cluster" in r.kubernetes_kinds}
    if typed_clusters != set(data.cluster_modes):
        errors.append("kubernetes: every cluster type needs exactly one cluster mode")


def check_representation(record: CatalogRecord, data: Catalog, errors: list[str]) -> None:
    item = record.representation
    if item.kind == "labeled_boundary" and item.asset and item.asset not in data.assets:
        errors.append(f"{record.id}: boundary icon {item.asset} is not in the manifest")
    if item.kind == "native_class":
        pack = data.packs.get(item.pack or "")
        if not item.class_path or pack is None:
            errors.append(f"{record.id}: native class needs a class path and a known pack")
        elif pack.status != "approved" or pack.distribution != "dependency":
            errors.append(f"{record.id}: native class pack is not an approved dependency")
    elif item.kind == "custom_asset":
        asset = data.assets.get(item.asset or "")
        if asset is None:
            errors.append(f"{record.id}: custom asset {item.asset} is not in the manifest")
        elif not (item.label or "").startswith(asset.required_label):
            errors.append(f"{record.id}: label must keep the asset's required label")
    elif item.kind == "blocked":
        pack = data.packs.get(item.pack or "")
        if pack is None or pack.status != "blocked" or item.blocker != pack.blocker:
            errors.append(f"{record.id}: a blocked type must name an open blocker on its pack")
        if record.status != "semantics_only":
            errors.append(f"{record.id}: a blocked type cannot be marked fully supported")
    elif not item.label:
        errors.append(f"{record.id}: a labeled representation needs a label")
    if item.kind != "blocked" and record.status == "semantics_only":
        errors.append(f"{record.id}: semantics_only is reserved for blocked representations")
    check_private_record(record, data, errors)
    # FR-013: a Huawei service never gets a generic stand-in or an unapproved icon.
    if "huawei" in record.providers and len(record.providers) == 1 and record.entity == "resource":
        if item.kind == "native_class":
            errors.append(f"{record.id}: Huawei services must not use a substitute native class")
        if item.kind == "custom_asset" and item.asset in data.assets:
            if not data.assets[item.asset].pack.startswith("huawei-"):
                errors.append(f"{record.id}: Huawei services must not use another pack's asset")
        if item.kind == "labeled_node":
            errors.append(f"{record.id}: Huawei services must not use a generic labeled node")


def check_private_record(record: CatalogRecord, data: Catalog, errors: list[str]) -> None:
    asset = data.assets.get(record.representation.asset or "")
    pack = data.packs.get(asset.pack) if asset else None
    private_pack = pack is not None and pack.status == "private_use_only"
    if private_pack != (record.status == "private_use_only"):
        errors.append(f"{record.id}: private_use_only must match the icon's private-use pack")
    if asset is None or not private_pack:
        return
    if record.providers != ("huawei",):
        errors.append(f"{record.id}: a private-use pack serves only its own provider")
    # No guessing: the source title must name this service, not merely resemble it.
    for title in asset.symbols:
        tokens = re.findall(r"[a-z0-9]+", title.lower())
        code = (record.native_id or "").lower()
        if code not in tokens and record.display_name.lower() not in title.lower():
            errors.append(f"{record.id}: source title {title!r} does not name this service")


def check_source(source: str, owner: str, errors: list[str], root: Path = ROOT) -> None:
    if source.startswith("doc:"):
        name, _, fragment = source.removeprefix("doc:").partition("#")
        path = root / DOCUMENTS.get(name, "missing")
        if not path.exists() or fragment not in anchors(path.read_text()):
            errors.append(f"{owner}: {source} does not resolve")
    elif not source.startswith("https://"):
        errors.append(f"{owner}: source must be an https URL or a doc reference: {source}")


def check_inventory(data: Catalog, errors: list[str], root: Path = ROOT) -> dict[str, int]:
    text = (root / "doc/requirements/requirements.md").read_text()
    required = requirement_items(text)
    counts: dict[str, int] = {}
    for provider, items in required.items():
        mapped = data.inventory.get(provider, {})
        if set(items) != set(mapped):
            errors.append(
                f"inventory/{provider}: differs from requirements section 6: "
                f"{sorted(set(items) ^ set(mapped))}"
            )
        for item, types in mapped.items():
            if not types:
                errors.append(f"inventory/{provider}: {item} resolves to nothing")
            for type_id in types:
                record = data.records.get(type_id)
                if record is None or provider not in record.providers:
                    errors.append(f"inventory/{provider}: {item} -> {type_id} does not resolve")
        counts[provider] = len(mapped)
    baseline = text.split("Initial taxonomy IDs", 1)[1].split("```")[1]
    if set(re.findall(r"[a-z_]+\.[a-z_]+", baseline)) != set(data.taxonomy_ids):
        errors.append("taxonomy: the catalog and requirements section 5 list different IDs")
    return counts


def check_native_icons(data: Catalog, errors: list[str]) -> dict[str, int]:
    lock = json.loads((DATA / "native_icons.json").read_text())
    if lock["package_version"] != version("diagrams"):
        errors.append("native icons: the lock and the installed diagrams version differ")
    expected = {
        record.representation.class_path: record.representation.pack
        for record in data.records.values()
        if record.representation.kind == "native_class"
    }
    expected[data.fallback.class_path] = data.fallback.pack
    if set(lock["icons"]) != set(expected):
        errors.append("native icons: the lock and the catalog list different classes")
    counts: dict[str, int] = {}
    for class_path, pack in expected.items():
        assert class_path
        entry = lock["icons"].get(class_path)
        try:
            path = locate(class_path)
            if entry is None or entry["pack"] != pack or entry["sha256"] != sha256(path):
                errors.append(f"native icons: {class_path} differs from the pinned package")
        except (ImportError, AttributeError, OSError):
            errors.append(f"native icons: {class_path} does not resolve in the pinned package")
        counts[str(pack)] = counts.get(str(pack), 0) + 1
    return counts


def check_packs(data: Catalog, errors: list[str], root: Path = ROOT) -> None:
    for pack in data.manifest.packs:
        for terms in pack.terms:
            if not terms.url.startswith("https://") or not terms.summary:
                errors.append(f"{pack.id}: every term needs a source URL and a summary")
        if pack.status == "approved":
            if not (pack.attribution and pack.redistribution_evidence):
                errors.append(f"{pack.id}: approval needs attribution and redistribution evidence")
            if pack.rights_basis in {"none", "owner_risk_acceptance"}:
                errors.append(f"{pack.id}: approval needs a rights basis from a rights holder")
            if pack.blocker:
                errors.append(f"{pack.id}: an approved pack cannot carry a blocker")
            if pack.distribution == "none":
                errors.append(f"{pack.id}: an approved pack must say how it is delivered")
        elif pack.status == "blocked":
            if not (pack.blocker and pack.blocker_reason):
                errors.append(f"{pack.id}: a blocked pack must name its blocker and reason")
            if pack.distribution != "none":
                errors.append(f"{pack.id}: a blocked pack cannot be distributed")
            check_decision(pack.id, pack.blocker, errors, root)
        else:
            check_private_pack(pack, errors, root)
        if pack.distribution == "bundled":
            licensed = pack.status == "approved" and bool(pack.license)
            if not (licensed or pack.status == "private_use_only") or not pack.source_commit:
                errors.append(f"{pack.id}: bundling needs an approved, licensed, pinned source")
            if not (pack.source_sha256 or pack.source_files):
                errors.append(f"{pack.id}: bundling needs the original source hash")


def check_decision(owner: str, identifier: str | None, errors: list[str], root: Path) -> str | None:
    decisions = (root / "doc/project-management/decisions.md").read_text()
    match = re.search(rf"^\| {identifier} \|.*$", decisions, re.MULTILINE)
    if identifier is None or match is None:
        errors.append(f"{owner}: {identifier} is not in the decision log")
        return None
    return match.group(0)


def check_private_pack(pack: Pack, errors: list[str], root: Path) -> None:
    """Risk acceptance is not a license, so nothing here may read as cleared."""
    if pack.rights_basis != "owner_risk_acceptance":
        errors.append(f"{pack.id}: private use must rest on the owner's recorded risk acceptance")
    if pack.license or pack.redistribution_evidence:
        errors.append(f"{pack.id}: private use cannot claim a license or redistribution evidence")
    if not pack.attribution or not pack.source_files:
        errors.append(f"{pack.id}: private use still needs attribution and a pinned source")
    if pack.blocker_scope != "public_distribution" or not pack.blocker_reason:
        errors.append(f"{pack.id}: public distribution must stay an explicit blocker")
    check_decision(pack.id, pack.blocker, errors, root)
    decision = check_decision(pack.id, pack.owner_decision, errors, root)
    if decision and PRIVATE_PHRASE not in decision.lower():
        errors.append(f"{pack.id}: {pack.owner_decision} does not limit use to {PRIVATE_PHRASE}")


def check_private_use(
    manifest: AssetManifest,
    errors: list[str],
    root: Path = ROOT,
    environ: Mapping[str, str] = os.environ,
) -> str:
    """Keep private-use icons from leaving through a package upload or a public repository."""
    if not any(pack.status == "private_use_only" for pack in manifest.packs):
        return "no_private_use_assets"
    project = tomllib.loads((root / "pyproject.toml").read_text())["project"]
    if PRIVATE_CLASSIFIER not in project.get("classifiers", []):
        errors.append(f"pyproject.toml: private-use assets require {PRIVATE_CLASSIFIER!r}")
    readme = (root / "plugins/cloud-architecture-diagrams/README.md").read_text().lower()
    if PRIVATE_PHRASE not in readme:
        errors.append(f"plugin README must state that it is for {PRIVATE_PHRASE}")
    path = environ.get("GITHUB_EVENT_PATH")
    if environ.get("GITHUB_ACTIONS") != "true" or not path:
        return "not_checked_outside_actions"
    try:
        private = json.loads(Path(path).read_text())["repository"]["private"]
    except (OSError, ValueError, KeyError, TypeError):
        errors.append("repository visibility could not be read from the Actions event")
        return "unreadable"
    if private is not True:
        errors.append("this repository is public: private-use assets must not be published here")
        return "public"
    return "private"


def svg_problems(path: Path) -> list[str]:
    raw = path.read_bytes()
    if re.search(rb"(?i)<!doctype|<!entity|<\?xml-stylesheet", raw):
        return ["a document type, entity or stylesheet declaration is not allowed"]
    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        return ["not well-formed XML"]
    problems = []
    for element in root.iter():
        tag = element.tag.rpartition("}")[2]
        if tag not in SVG_ELEMENTS:
            problems.append(f"element {tag} is not allowed")
        for name, value in element.attrib.items():
            if name.rpartition("}")[2] not in SVG_ATTRIBUTES:
                problems.append(f"attribute {name} is not allowed")
            # Only a fragment inside the same file may be referenced, as a clip path does here.
            internal = re.fullmatch(r"url\(#[A-Za-z0-9_-]+\)", value)
            if not internal and name != "xmlns":
                if re.search(r"(?i)url\(|https?:|javascript:|data:", value):
                    problems.append(f"attribute {name} holds an external reference")
    return problems


def png_size(path: Path) -> tuple[int, int] | None:
    head = path.read_bytes()[:24]
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return int.from_bytes(head[16:20]), int.from_bytes(head[20:24])


def check_assets(
    manifest: AssetManifest, errors: list[str], package: Path = PACKAGE, repo: Path = ROOT
) -> dict[str, str]:
    packs = {pack.id: pack for pack in manifest.packs}
    listed: dict[str, str] = {}
    concepts = set()
    subset = repo / "assets-source/drawio/networks-subset.xml"
    shapes = load_shapes(subset) if subset.exists() else {}
    for asset in manifest.assets:
        pack = packs.get(asset.pack)
        if pack is None or pack.status == "blocked" or pack.distribution != "bundled":
            errors.append(f"{asset.id}: its pack does not permit bundling")
        if asset.pack == "drawio-network-2018":
            concepts.add(asset.concept)
        elif asset.derived.svg is None or any(
            item.sha256 != asset.derived.svg.sha256 for item in asset.original
        ):
            errors.append(f"{asset.id}: recorded as unchanged, but its digests differ")
        for file in filter(None, (asset.derived.svg, asset.derived.png)):
            listed[file.path] = file.sha256
            path = package / file.path
            if not path.is_file() or path.is_symlink():
                errors.append(f"{asset.id}: {file.path} is missing or a symbolic link")
            elif sha256(path) != file.sha256:
                errors.append(f"{asset.id}: {file.path} does not match its recorded hash")
        svg = package / asset.derived.svg.path if asset.derived.svg else None
        if svg and svg.is_file():
            for problem in svg_problems(svg):
                errors.append(f"{asset.id}: unsafe SVG: {problem}")
        png = package / asset.derived.png.path
        if png.is_file():
            size = png_size(png)
            if size is None or size != (asset.derived.png.width, asset.derived.png.height):
                errors.append(f"{asset.id}: PNG header differs from its record")
        for original in asset.original:
            if original.digest_of != "canonical_stencil_xml":
                continue
            shape = shapes.get(original.name)
            if shape is None or shape_digest(shape) != original.sha256:
                errors.append(f"{asset.id}: original shape {original.name} does not match")
        if asset.id in CONCEPTS and shapes and svg and svg.is_file():
            if compose(asset.id, shapes)[0] != svg.read_text():
                errors.append(f"{asset.id}: SVG does not reproduce from the audited source")
    if concepts != REQUIRED_CONCEPTS:
        errors.append(f"assets: D-010 concepts differ: {sorted(concepts ^ REQUIRED_CONCEPTS)}")
    listed |= check_fonts(manifest, errors, package)
    if subset.exists():
        names = {shape.attrib["name"] for shape in ET.parse(subset).getroot()}
        if names != set(SHAPES):
            errors.append("assets: the source subset holds other shapes than the audited seven")
    # The plugin ships src through a symlink, so anything here reaches every install (D-015).
    for path in sorted(package.rglob("*")):
        if path.is_dir() or "__pycache__" in path.parts:
            continue
        relative = str(path.relative_to(package))
        if path.suffix.lower() in ASSET_SUFFIXES and relative not in listed:
            errors.append(f"{relative}: visual asset is not in the rights manifest")
    notice = package / "assets/NOTICE.md"
    if not notice.is_file():
        errors.append("assets: NOTICE.md is missing from the package")
    else:
        text = notice.read_text()
        for pack in manifest.packs:
            if pack.distribution == "bundled" and "CC BY 4.0" not in text:
                errors.append(f"{pack.id}: NOTICE.md lacks its license")
        if "O-002" not in text or PRIVATE_PHRASE not in text.lower():
            errors.append("assets: NOTICE.md must disclose the private-use limit and O-002")
        if "D-018" not in text or "not cleared" not in text.lower():
            errors.append("assets: NOTICE.md must say the D-018 rights are not cleared")
        if manifest.fonts and "SIL Open Font License" not in text:
            errors.append("assets: NOTICE.md must name the license of the bundled fonts")
        # FR-052: icons delivered by `diagrams` are not bundled, so their terms live only here.
        for source in ("AWS", "Azure", "Google Cloud", "Kubernetes", "mingrammer/diagrams"):
            if not re.search(rf"^\|.*{re.escape(source)}", text, re.M):
                errors.append(f"assets: NOTICE.md must state the terms for {source} icons")
    return listed


def check_fonts(manifest: AssetManifest, errors: list[str], package: Path) -> dict[str, str]:
    """The renderer bundles these so that layout and Thai glyphs do not depend on the host."""
    if {font.family for font in manifest.fonts} != REQUIRED_FONTS:
        errors.append(f"fonts: the manifest must list exactly {sorted(REQUIRED_FONTS)}")
    listed: dict[str, str] = {}
    for font in manifest.fonts:
        listed[font.path] = font.sha256
        path = package / font.path
        if not path.is_file() or path.is_symlink():
            errors.append(f"{font.family}: {font.path} is missing or a symbolic link")
        elif sha256(path) != font.sha256:
            errors.append(f"{font.family}: {font.path} does not match its recorded hash")
        notice = package / font.license_path
        if not font.source_url.startswith("https://") or not font.license:
            errors.append(f"{font.family}: a font needs a source URL and a license")
        if not notice.is_file() or "SIL OPEN FONT LICENSE" not in notice.read_text().upper():
            errors.append(f"{font.family}: the font's license notice must ship with it")
    return listed


def check_pack_inventory(manifest: AssetManifest, errors: list[str], root: Path = ROOT) -> int:
    """A private-use asset must be exactly the pinned pack's entry that its record names."""
    inventory = json.loads((root / PACK_INVENTORY).read_text())
    rows = {(row["file"], row["index"]): row for row in inventory["entries"]}
    pack = next(item for item in manifest.packs if item.status == "private_use_only")
    pinned = [item.model_dump() for item in pack.source_files]
    if inventory["commit"] != pack.source_commit or inventory["files"] != pinned:
        errors.append("pack inventory: its pin differs from the rights manifest")
    for asset in manifest.assets:
        if asset.pack != pack.id:
            continue
        for original in asset.original:
            row = rows.get((original.source_path, original.entry_index))
            if row is None or (row["title"], row["sha256"]) != (original.name, original.sha256):
                errors.append(f"{asset.id}: not the pinned entry named {original.name}")
    return len(rows)


def icon_coverage(data: Catalog) -> dict[str, list[str]]:
    """Group each required Huawei item by its real icon state, with no partial credit."""
    groups: dict[str, list[str]] = {"mapped": [], "labeled_boundary": [], "no_clear_match": []}
    for item, types in data.inventory["huawei"].items():
        records = [data.records[type_id] for type_id in types]
        if any(record.representation.kind == "blocked" for record in records):
            groups["no_clear_match"].append(item)
        elif all(record.representation.asset for record in records):
            groups["mapped"].append(item)
        else:
            groups["labeled_boundary"].append(item)
    return groups


def check_plugin(errors: list[str], root: Path = ROOT) -> None:
    link = root / "plugins/cloud-architecture-diagrams/src"
    if not link.is_symlink() or link.resolve() != root / "src":
        errors.append("plugin: src must stay a link to the checked package")
    for path in (root / "plugins/cloud-architecture-diagrams").rglob("*"):
        if path.is_file() and not path.is_symlink() and path.suffix.lower() in ASSET_SUFFIXES:
            if "src" not in path.relative_to(root / "plugins/cloud-architecture-diagrams").parts:
                errors.append(f"{path.name}: visual asset outside the checked package")


def check_source_evidence(data: Catalog, errors: list[str], root: Path = ROOT) -> int:
    path = root / SOURCE_CHECKS
    checked = {item["url"] for item in json.loads(path.read_text())["pages"]}
    urls = {source for record in data.records.values() for source in record.sources}
    urls |= {source for rule in data.rules.values() for source in rule.sources}
    urls |= {terms.url for pack in data.manifest.packs for terms in pack.terms}
    for file in data.files.values():
        urls |= {url for url in (file.label_source, file.verified_release_source) if url}
    urls = {url for url in urls if url.startswith("https://")}
    for rule in data.rules.values():
        for source in rule.sources:
            check_source(source, rule.code, errors, root)
    for url in sorted(urls - checked):
        errors.append(f"evidence: {url} has no recorded source check")
    return len(urls)


def third_party_errors(package: Path, root: Path = ROOT) -> list[str]:
    """NFR-004: the Python packages the core installs must match the shipped inventory."""
    inventory = package / "assets/THIRD-PARTY-PYTHON.md"
    if not inventory.is_file():
        return ["assets: THIRD-PARTY-PYTHON.md is missing from the package"]
    lock = tomllib.loads((root / "uv.lock").read_text())
    listed = {
        match[0]: (match[1], match[2].strip())
        for match in re.findall(
            r"^\| ([a-z0-9._-]+) \| ([^ |]+) \| ([^|]+) \|$", inventory.read_text(), re.M
        )
    }
    locked = runtime_packages(lock)
    errors = [
        f"{name}: installed at runtime but not in the inventory"
        for name in locked.keys() - listed.keys()
    ]
    errors += [
        f"{name}: in the inventory but not installed at runtime"
        for name in listed.keys() - locked.keys()
    ]
    errors += [
        f"{name}: inventory says {listed[name][0]}, lock says {locked[name]}"
        for name in locked.keys() & listed.keys()
        if listed[name][0] != locked[name]
    ]
    errors += [
        f"{name}: the inventory states no license" for name, row in listed.items() if not row[1]
    ]
    return sorted(errors)


def run(root: Path = ROOT) -> tuple[list[str], dict[str, object]]:
    errors: list[str] = []
    data = catalog()
    published = json.loads((root / "schemas/catalog-v1.schema.json").read_text())
    if published != ProviderFile.model_json_schema():
        errors.append("schemas/catalog-v1.schema.json differs from the catalog model")
    check_records(data, errors)
    inventory = check_inventory(data, errors, root)
    native = check_native_icons(data, errors)
    check_packs(data, errors, root)
    listed = check_assets(data.manifest, errors, root / "src/cloud_architecture_diagrams", root)
    errors += third_party_errors(root / "src/cloud_architecture_diagrams", root)
    visibility = check_private_use(data.manifest, errors, root)
    pack_entries = check_pack_inventory(data.manifest, errors, root)
    check_plugin(errors, root)
    urls = check_source_evidence(data, errors, root)
    report: dict[str, object] = {
        "catalog_version": data.version,
        "passed": not errors,
        "errors": errors,
        "records": len(data.records),
        "taxonomy": len(data.taxonomy_ids),
        "rules": len(data.rules),
        "required_items": inventory,
        "native_icons_by_pack": native,
        "bundled_asset_sha256": listed,
        "packs": {
            pack.id: {
                "status": pack.status,
                "distribution": pack.distribution,
                "rights_basis": pack.rights_basis,
            }
            for pack in data.manifest.packs
        },
        "release_blockers": data.release_blockers(),
        "huawei_icon_coverage": icon_coverage(data),
        "huawei_pack_entries": pack_entries,
        "repository_visibility": visibility,
        "checked_source_urls": urls,
    }
    return errors, report


def main() -> int:
    importlib.import_module("diagrams")
    errors, report = run()
    reports = ROOT / "reports"
    reports.mkdir(exist_ok=True)
    (reports / "catalog-license.json").write_text(json.dumps(report, indent=2) + "\n")
    for error in errors:
        print(error)
    print(json.dumps({key: report[key] for key in ("passed", "records", "rules", "taxonomy")}))
    if errors:
        return 1
    import pytest

    return int(
        pytest.main(
            ["tests/test_catalog_license.py", "--junitxml=reports/catalog-license-tests.xml", "-q"]
        )
    )


if __name__ == "__main__":
    sys.exit(main())
