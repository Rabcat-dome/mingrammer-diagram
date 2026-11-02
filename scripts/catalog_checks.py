"""M2-05 catalog, inventory and license gate. Missing rights, assets or mappings fail the lane."""

import hashlib
import importlib
import json
import re
import sys
import xml.etree.ElementTree as ET
from importlib.metadata import version
from pathlib import Path
from typing import get_args

from build_native_icon_lock import locate
from build_onprem_assets import CONCEPTS, SHAPES, compose, load_shapes, shape_digest
from repository_checks import anchors

from cloud_architecture_diagrams.catalog import (
    DATA,
    AssetManifest,
    Catalog,
    CatalogRecord,
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
SVG_ELEMENTS = {"svg", "g", "path", "rect", "ellipse"}
SVG_ATTRIBUTES = {
    "xmlns", "viewBox", "width", "height", "transform", "d", "x", "y", "rx", "ry", "cx", "cy",
    "fill", "stroke", "stroke-width", "stroke-dasharray",
}  # fmt: skip
DOCUMENTS = {
    "requirements": "doc/requirements/requirements.md",
    "s02-additional": "doc/project-management/evidence/S02-additional-icon-sources.md",
}
REQUIRED_CONCEPTS = {
    "Load balancer", "Hypervisor", "VM", "NAS", "SAN", "Identity service", "Backup system",
    "Monitoring",
}  # fmt: skip
SOURCE_CHECKS = "doc/project-management/evidence/S06-source-checks.json"


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
        elif item.label != asset.required_label:
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
    # FR-013: a Huawei service never gets a generic stand-in or an unapproved icon.
    if "huawei" in record.providers and len(record.providers) == 1 and record.entity == "resource":
        if item.kind == "native_class":
            errors.append(f"{record.id}: Huawei services must not use a substitute native class")
        if (
            item.kind == "custom_asset"
            and data.assets[item.asset or ""].pack != "huawei-cloud-icons"
        ):
            errors.append(f"{record.id}: Huawei services must not use another pack's asset")
        if item.kind == "labeled_node":
            errors.append(f"{record.id}: Huawei services must not use a generic labeled node")


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
            if pack.rights_basis == "none":
                errors.append(f"{pack.id}: approval needs a rights basis")
            if pack.blocker:
                errors.append(f"{pack.id}: an approved pack cannot carry a blocker")
            if pack.distribution == "none":
                errors.append(f"{pack.id}: an approved pack must say how it is delivered")
        else:
            if not (pack.blocker and pack.blocker_reason):
                errors.append(f"{pack.id}: a blocked pack must name its blocker and reason")
            if pack.distribution != "none":
                errors.append(f"{pack.id}: a blocked pack cannot be distributed")
            decisions = (root / "doc/project-management/decisions.md").read_text()
            if not re.search(rf"^\| {pack.blocker} \|", decisions, re.MULTILINE):
                errors.append(f"{pack.id}: {pack.blocker} is not in the decision log")
        if pack.distribution == "bundled":
            if pack.status != "approved" or not pack.license or not pack.source_commit:
                errors.append(f"{pack.id}: bundling needs an approved, licensed, pinned source")
            if not pack.source_sha256:
                errors.append(f"{pack.id}: bundling needs the original source hash")


def svg_problems(path: Path) -> list[str]:
    try:
        root = ET.parse(path).getroot()
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
            if re.search(r"(?i)url\(|https?:|javascript:|data:", value) and name != "xmlns":
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
        if pack is None or pack.status != "approved" or pack.distribution != "bundled":
            errors.append(f"{asset.id}: its pack does not permit bundling")
        concepts.add(asset.concept)
        for file in (asset.derived.svg, asset.derived.png):
            listed[file.path] = file.sha256
            path = package / file.path
            if not path.is_file() or path.is_symlink():
                errors.append(f"{asset.id}: {file.path} is missing or a symbolic link")
            elif sha256(path) != file.sha256:
                errors.append(f"{asset.id}: {file.path} does not match its recorded hash")
        svg = package / asset.derived.svg.path
        if svg.is_file():
            for problem in svg_problems(svg):
                errors.append(f"{asset.id}: unsafe SVG: {problem}")
        png = package / asset.derived.png.path
        if png.is_file():
            size = png_size(png)
            if size is None or size != (asset.derived.png.width, asset.derived.png.height):
                errors.append(f"{asset.id}: PNG header differs from its record")
        for original in asset.original:
            shape = shapes.get(original.name)
            if shape is None or shape_digest(shape) != original.canonical_sha256:
                errors.append(f"{asset.id}: original shape {original.name} does not match")
        if asset.id in CONCEPTS and shapes and svg.is_file():
            if compose(asset.id, shapes)[0] != svg.read_text():
                errors.append(f"{asset.id}: SVG does not reproduce from the audited source")
    if concepts != REQUIRED_CONCEPTS:
        errors.append(f"assets: D-010 concepts differ: {sorted(concepts ^ REQUIRED_CONCEPTS)}")
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
        if "O-002" not in text:
            errors.append("assets: NOTICE.md must disclose the Huawei blocker")
    return listed


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
