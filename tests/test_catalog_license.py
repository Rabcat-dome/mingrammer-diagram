"""M2-05 catalog-license lane: FR-050..055, NFR-004. Each check must reject what it guards against."""

import json
import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import catalog_checks  # noqa: E402

from cloud_architecture_diagrams import cli  # noqa: E402
from cloud_architecture_diagrams.catalog import (  # noqa: E402
    MAX_RESULTS,
    AssetManifest,
    Catalog,
    catalog,
)

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "src/cloud_architecture_diagrams"
ONE_PIXEL_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d4948445200000001000000010806000000" + "1f15c4890000000d49444154"
    "789c6300010000000500010d0a2db40000000049454e44ae426082"
)


def manifest_data() -> dict[str, Any]:
    value: dict[str, Any] = json.loads((PACKAGE / "catalog_data/assets.json").read_text())
    return value


def rebuilt(data: dict[str, Any]) -> AssetManifest:
    return AssetManifest.model_validate_json(json.dumps(data))


@pytest.fixture
def package(tmp_path: Path) -> Path:
    """A throwaway copy of the package, so a tampering test cannot touch the real assets."""
    copy = tmp_path / "package"
    shutil.copytree(PACKAGE, copy, ignore=shutil.ignore_patterns("__pycache__"))
    return copy


def asset_errors(manifest: AssetManifest, package: Path) -> list[str]:
    errors: list[str] = []
    catalog_checks.check_assets(manifest, errors, package, ROOT)
    return errors


def pack_errors(mutate: Callable[[dict[str, Any]], None]) -> list[str]:
    data = manifest_data()
    mutate(data)
    errors: list[str] = []
    view = Catalog()
    view.manifest = rebuilt(data)
    catalog_checks.check_packs(view, errors)
    return errors


def pack(data: dict[str, Any], identifier: str) -> dict[str, Any]:
    found: dict[str, Any] = next(item for item in data["packs"] if item["id"] == identifier)
    return found


def test_repository_passes_every_catalog_and_license_check() -> None:
    errors, report = catalog_checks.run()
    assert errors == []
    assert report["passed"] is True
    assert report["records"] == len(catalog().records) and catalog().records
    assert report["rules"] == len(catalog().rules) and catalog().rules
    required = report["required_items"]
    assert isinstance(required, dict) and set(required) == {
        "aws",
        "azure",
        "gcp",
        "huawei",
        "onprem",
    }


def test_published_catalog_schema_matches_the_model() -> None:
    from cloud_architecture_diagrams.catalog import ProviderFile

    published = json.loads((ROOT / "schemas/catalog-v1.schema.json").read_text())
    assert published == ProviderFile.model_json_schema()


def test_a_missing_required_item_fails_inventory() -> None:
    view = Catalog()
    del view.inventory["aws"]["CloudWatch"]
    errors: list[str] = []
    catalog_checks.check_inventory(view, errors)
    assert any("differs from requirements" in error for error in errors)


def test_an_item_resolving_to_nothing_fails_inventory() -> None:
    view = Catalog()
    view.inventory["azure"]["NIC"] = ["azure.network.not_a_type"]
    errors: list[str] = []
    catalog_checks.check_inventory(view, errors)
    assert any("does not resolve" in error for error in errors)


def test_an_item_from_another_provider_fails_inventory() -> None:
    view = Catalog()
    view.inventory["gcp"]["IAM"] = ["aws.identity.iam"]
    errors: list[str] = []
    catalog_checks.check_inventory(view, errors)
    assert any("does not resolve" in error for error in errors)


def test_requirement_tables_parse_to_every_named_item() -> None:
    text = (ROOT / "doc/requirements/requirements.md").read_text()
    items = catalog_checks.requirement_items(text)
    assert "Shared VPC host/service-project references" in items["gcp"]
    assert "enterprise-project context where applicable" in items["huawei"]
    assert len(items["aws"]) == 17 and len(items["azure"]) == 19 and len(items["onprem"]) == 20


def test_native_class_outside_the_pinned_package_fails() -> None:
    view = Catalog()
    record = view.records["aws.compute.ec2"]
    representation = record.representation.model_copy(update={"class_path": "diagrams.aws.Fake"})
    view.records["aws.compute.ec2"] = record.model_copy(update={"representation": representation})
    errors: list[str] = []
    catalog_checks.check_native_icons(view, errors)
    assert any("Fake" in error for error in errors)


def test_changed_native_icon_digest_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    errors: list[str] = []
    monkeypatch.setattr(catalog_checks, "sha256", lambda path: "0" * 64)
    catalog_checks.check_native_icons(catalog(), errors)
    assert any("differs from the pinned package" in error for error in errors)


def test_huawei_generic_substitution_fails() -> None:
    view = Catalog()
    record = view.records["huawei.compute.ecs"]
    for representation in (
        record.representation.model_copy(
            update={
                "kind": "native_class",
                "class_path": "diagrams.generic.compute.Rack",
                "pack": "diagrams-generic",
                "blocker": None,
            }
        ),
        record.representation.model_copy(
            update={"kind": "labeled_node", "label": "ECS", "pack": None, "blocker": None}
        ),
    ):
        errors: list[str] = []
        catalog_checks.check_representation(
            record.model_copy(update={"representation": representation, "status": "supported"}),
            view,
            errors,
        )
        assert any("Huawei services must not" in error for error in errors), representation.kind


MAPPED = {
    "huawei.network.vpc": "Virtual Private Cloud (VPC)",
    "huawei.compute.ecs": "Elastic Cloud Server (ECS)",
    "huawei.network.elb": "Elastic Load Balance (ELB)",
    "huawei.network.eip": "Elastic IP (EIP)",
    "huawei.network.nat_gateway": "NAT Gateway",
    "huawei.containers.cce_standard": "Cloud Container Engine (CCE)",
    "huawei.containers.cce_turbo": "Cloud Container Engine (CCE)",
    "huawei.containers.cce_autopilot": "Cloud Container Engine (CCE)",
    "huawei.database.rds": "Relational Database Service (RDS)",
    "huawei.storage.obs": "Object Storage Service (OBS)",
    "huawei.identity.iam": "Identity and Access Management (IAM)",
    "huawei.integration.api_gateway": "API Gateway (APIG)",
    "huawei.compute.functiongraph": "FunctionGraph",
    "huawei.network.vpn": "Virtual Private Network (VPN)",
    "huawei.network.direct_connect": "Direct Connect",
    "huawei.observability.cloud_eye": "Cloud Eye Service (CES)",
    "huawei.observability.lts": "Log Tank Servce (LTS)",
}


def test_huawei_icons_map_only_exact_titles() -> None:
    # Changing this table is a mapping decision that the owner must be told about by name.
    records = catalog().records
    for type_id, title in MAPPED.items():
        record = records[type_id]
        asset = catalog().assets[str(record.representation.asset)]
        assert asset.symbols == (title,) and record.status == "private_use_only"
        assert asset.pack == "huawei-latam-color"
        assert asset.derived.svg is not None
        assert asset.original[0].sha256 == asset.derived.svg.sha256
    assert not [
        record.id
        for record in records.values()
        if record.providers == ("huawei",) and record.representation.kind == "blocked"
    ]


def test_required_huawei_items_are_reported_by_name() -> None:
    coverage = catalog_checks.icon_coverage(catalog())
    assert coverage["no_clear_match"] == []
    assert {"subnet", "Security Group"} <= set(coverage["labeled_boundary"])
    assert set(coverage["mapped"]) == {
        "VPC",
        "ECS",
        "ELB",
        "EIP",
        "NAT Gateway",
        "CCE",
        "RDS",
        "OBS",
        "IAM",
        "API Gateway",
        "FunctionGraph",
        "VPN",
        "Direct Connect",
        "Cloud Eye",
        "LTS",
    }


def test_the_only_blocker_is_public_distribution() -> None:
    [blocker] = catalog().release_blockers()
    assert blocker["id"] == "O-002" and blocker["scope"] == "public_distribution"
    assert blocker["affected_types"] == sorted(MAPPED)
    assert "no redistribution permission" in str(blocker["reason"])


def test_replaced_line_art_pack_is_gone_from_the_package() -> None:
    assert "huawei-juandiaz00-png" not in catalog().packs
    assert not [asset for asset in catalog().manifest.assets if "juandiaz" in asset.pack]
    bundled = {asset.derived.png.path for asset in catalog().manifest.assets}
    assert {
        str(path.relative_to(PACKAGE)) for path in (PACKAGE / "assets/huawei").glob("*.png")
    } <= (bundled)


def test_every_bundled_asset_is_used_by_a_catalog_type() -> None:
    # An unused icon would be an unjustified copy of material whose rights are not cleared.
    used = {record.representation.asset for record in catalog().records.values()}
    assert {asset.id for asset in catalog().manifest.assets} <= used


def private_record(type_id: str, **updates: Any) -> tuple[Any, Catalog]:
    view = Catalog()
    return view.records[type_id].model_copy(update=updates), view


@pytest.mark.parametrize(
    ("type_id", "title"),
    [
        ("huawei.storage.obs", "storage-55"),
        ("huawei.containers.cce_standard", "other-cluster-computing-platform-services"),
        ("huawei.observability.lts", "log-and-trace-consolele"),
        ("huawei.network.direct_connect", "cc-21"),
        ("huawei.observability.cloud_eye", "cmc"),
        ("huawei.network.nat_gateway", "Network Gateway"),
    ],
)
def test_a_title_that_does_not_name_the_service_cannot_be_mapped(type_id: str, title: str) -> None:
    # These are the tempting guesses, so each must fail however it is written down.
    view = Catalog()
    view.assets["guess"] = view.assets["huawei-ecs"].model_copy(
        update={"id": "guess", "symbols": (title,)}
    )
    record = view.records[type_id]
    item = record.representation.model_copy(update={"asset": "guess"})
    errors: list[str] = []
    catalog_checks.check_private_record(
        record.model_copy(update={"representation": item}), view, errors
    )
    assert any("does not name this service" in error for error in errors), errors


def test_private_pack_serves_only_its_provider() -> None:
    view = Catalog()
    record = view.records["onprem.storage.nas"]
    item = record.representation.model_copy(update={"asset": "huawei-rds"})
    errors: list[str] = []
    catalog_checks.check_representation(
        record.model_copy(update={"representation": item, "status": "private_use_only"}),
        view,
        errors,
    )
    assert any("serves only its own provider" in error for error in errors)


def test_private_status_must_match_the_pack() -> None:
    record, view = private_record("huawei.compute.ecs", status="supported")
    errors: list[str] = []
    catalog_checks.check_private_record(record, view, errors)
    assert any("private_use_only must match" in error for error in errors)


def private_pack_errors(mutate: Callable[[dict[str, Any]], None]) -> list[str]:
    def wrapped(data: dict[str, Any]) -> None:
        mutate(pack(data, "huawei-latam-color"))

    return pack_errors(wrapped)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("license", "MIT", "cannot claim a license"),
        ("redistribution_evidence", "Seems fine", "cannot claim a license"),
        ("rights_basis", "license", "recorded risk acceptance"),
        ("attribution", None, "attribution and a pinned source"),
        ("source_files", [], "attribution and a pinned source"),
        ("blocker_scope", "icon_coverage", "must stay an explicit blocker"),
        ("blocker", "O-999", "not in the decision log"),
        ("owner_decision", "D-999", "not in the decision log"),
        ("owner_decision", "D-001", "does not limit use"),
        ("source_commit", None, "pinned source"),
    ],
)
def test_private_use_pack_cannot_read_as_cleared(field: str, value: Any, message: str) -> None:
    errors = private_pack_errors(lambda item: item.update({field: value}))
    assert any(message in error for error in errors), errors


def test_owner_risk_acceptance_cannot_approve_a_pack() -> None:
    def mutate(item: dict[str, Any]) -> None:
        item.update({"status": "approved", "blocker": None, "redistribution_evidence": "Owner"})

    errors = private_pack_errors(mutate)
    assert any("from a rights holder" in error for error in errors), errors


def visibility_root(tmp_path: Path, classifiers: str, readme: str) -> Path:
    (tmp_path / "plugins/cloud-architecture-diagrams").mkdir(parents=True)
    (tmp_path / "pyproject.toml").write_text(f"[project]\nclassifiers = [{classifiers}]\n")
    (tmp_path / "plugins/cloud-architecture-diagrams/README.md").write_text(readme)
    return tmp_path


def test_private_use_requires_the_upload_block(tmp_path: Path) -> None:
    root = visibility_root(tmp_path, "", "For private personal use only.")
    errors: list[str] = []
    catalog_checks.check_private_use(catalog().manifest, errors, root, {})
    assert any("Do Not Upload" in error for error in errors)


def test_private_use_requires_the_plugin_to_say_so(tmp_path: Path) -> None:
    root = visibility_root(tmp_path, '"Private :: Do Not Upload"', "A plugin.")
    errors: list[str] = []
    catalog_checks.check_private_use(catalog().manifest, errors, root, {})
    assert any("plugin README" in error for error in errors)


@pytest.mark.parametrize(
    ("event", "state", "fails"),
    [
        ('{"repository": {"private": true}}', "private", False),
        ('{"repository": {"private": false}}', "public", True),
        ('{"repository": {}}', "unreadable", True),
        ("not json", "unreadable", True),
    ],
)
def test_public_repository_fails_the_lane(
    tmp_path: Path, event: str, state: str, fails: bool
) -> None:
    root = visibility_root(tmp_path, '"Private :: Do Not Upload"', "For private personal use only.")
    path = tmp_path / "event.json"
    path.write_text(event)
    errors: list[str] = []
    environ = {"GITHUB_ACTIONS": "true", "GITHUB_EVENT_PATH": str(path)}
    assert catalog_checks.check_private_use(catalog().manifest, errors, root, environ) == state
    assert bool(errors) == fails


def test_repository_visibility_is_disclosed_as_unchecked_outside_actions() -> None:
    errors: list[str] = []
    state = catalog_checks.check_private_use(catalog().manifest, errors, ROOT, {})
    assert state == "not_checked_outside_actions" and errors == []


def test_tampered_private_asset_fails_its_hash(package: Path) -> None:
    (package / "assets/huawei/ecs.png").write_bytes(ONE_PIXEL_PNG)
    (package / "assets/huawei/obs.svg").write_text("<svg xmlns='http://www.w3.org/2000/svg'/>")
    errors = asset_errors(catalog().manifest, package)
    assert any("ecs.png does not match" in error for error in errors)
    assert any("obs.svg does not match" in error for error in errors)


def test_private_asset_recorded_as_changed_fails(package: Path) -> None:
    data = manifest_data()
    asset = next(item for item in data["assets"] if item["id"] == "huawei-ecs")
    asset["original"][0]["sha256"] = "0" * 64
    errors = asset_errors(rebuilt(data), package)
    assert any("recorded as unchanged" in error for error in errors)


def test_pack_inventory_detects_the_wrong_entry() -> None:
    data = manifest_data()
    asset = next(item for item in data["assets"] if item["id"] == "huawei-ecs")
    asset["original"][0]["entry_index"] = 0
    errors: list[str] = []
    catalog_checks.check_pack_inventory(rebuilt(data), errors)
    assert any("not the pinned entry" in error for error in errors)
    pin = next(item for item in data["packs"] if item["id"] == "huawei-latam-color")
    pin["source_commit"] = "0" * 40
    errors = []
    catalog_checks.check_pack_inventory(rebuilt(data), errors)
    assert any("its pin differs" in error for error in errors)


def test_pack_inventory_holds_no_artwork() -> None:
    inventory = json.loads((ROOT / catalog_checks.PACK_INVENTORY).read_text())
    assert len(inventory["entries"]) == 90
    assert {tuple(sorted(row)) for row in inventory["entries"]} == {
        ("bytes", "file", "index", "sha256", "title")
    }


def test_notice_must_disclose_the_private_limit(package: Path) -> None:
    notice = package / "assets/NOTICE.md"
    notice.write_text(notice.read_text().replace("private personal use", "normal use"))
    errors = asset_errors(catalog().manifest, package)
    assert any("private-use limit" in error for error in errors)
    notice.write_text("O-002 private personal use, CC BY 4.0, rights are cleared.")
    errors = asset_errors(catalog().manifest, package)
    assert any("not cleared" in error for error in errors)


def test_approving_a_pack_without_evidence_fails() -> None:
    def mutate(data: dict[str, Any]) -> None:
        huawei = pack(data, "huawei-cloud-icons")
        huawei["status"] = "approved"

    errors = pack_errors(mutate)
    assert any("approval needs attribution" in error for error in errors)
    assert any("rights basis" in error for error in errors)
    assert any("cannot carry a blocker" in error for error in errors)


def test_bundled_pack_needs_license_and_pinned_source() -> None:
    def mutate(data: dict[str, Any]) -> None:
        drawio = pack(data, "drawio-network-2018")
        drawio["license"] = None
        drawio["source_commit"] = None
        drawio["source_sha256"] = None

    errors = pack_errors(mutate)
    assert any("approved, licensed, pinned" in error for error in errors)
    assert any("original source hash" in error for error in errors)


def test_blocked_pack_cannot_be_distributed_or_lose_its_decision() -> None:
    def mutate(data: dict[str, Any]) -> None:
        huawei = pack(data, "huawei-cloud-icons")
        huawei["distribution"] = "bundled"
        huawei["blocker"] = "O-999"

    errors = pack_errors(mutate)
    assert any("cannot be distributed" in error for error in errors)
    assert any("not in the decision log" in error for error in errors)


def test_terms_without_a_source_fail() -> None:
    def mutate(data: dict[str, Any]) -> None:
        pack(data, "aws-architecture-icons")["terms"][0]["url"] = "http://example.invalid/terms"

    assert any("source URL" in error for error in pack_errors(mutate))


def test_unlisted_asset_under_src_fails(package: Path) -> None:
    # Everything under src reaches the Claude plugin through its symlink (D-015).
    (package / "assets/huawei-ecs.png").write_bytes(ONE_PIXEL_PNG)
    errors = asset_errors(catalog().manifest, package)
    assert errors == ["assets/huawei-ecs.png: visual asset is not in the rights manifest"]


def test_asset_anywhere_under_src_fails(package: Path) -> None:
    (package / "catalog_data/logo.svg").write_text("<svg xmlns='http://www.w3.org/2000/svg'/>")
    errors = asset_errors(catalog().manifest, package)
    assert errors == ["catalog_data/logo.svg: visual asset is not in the rights manifest"]


def test_tampered_asset_fails_its_hash(package: Path) -> None:
    (package / "assets/onprem/nas.svg").write_text("<svg xmlns='http://www.w3.org/2000/svg'/>\n")
    (package / "assets/onprem/san.png").write_bytes(ONE_PIXEL_PNG)
    errors = asset_errors(catalog().manifest, package)
    assert any("nas.svg does not match" in error for error in errors)
    assert any("san.png does not match" in error for error in errors)
    assert any("PNG header differs" in error for error in errors)
    assert any("does not reproduce" in error for error in errors)


def test_missing_asset_fails(package: Path) -> None:
    (package / "assets/onprem/vm.png").unlink()
    assert any("missing" in error for error in asset_errors(catalog().manifest, package))


def test_linked_asset_fails(package: Path, tmp_path: Path) -> None:
    target = package / "assets/onprem/vm.png"
    outside = tmp_path / "outside.png"
    outside.write_bytes(target.read_bytes())
    target.unlink()
    target.symlink_to(outside)
    assert any("symbolic link" in error for error in asset_errors(catalog().manifest, package))


def test_missing_notice_fails(package: Path) -> None:
    (package / "assets/NOTICE.md").unlink()
    assert any("NOTICE.md" in error for error in asset_errors(catalog().manifest, package))


@pytest.mark.parametrize(
    "content",
    [
        '<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>',
        '<svg xmlns="http://www.w3.org/2000/svg"><image href="https://example.invalid/x"/></svg>',
        '<svg xmlns="http://www.w3.org/2000/svg" onload="alert(1)"/>',
        '<svg xmlns="http://www.w3.org/2000/svg"><rect fill="url(https://example.invalid)"/></svg>',
        '<svg xmlns="http://www.w3.org/2000/svg"><g clip-path="url(http://example.invalid#a)"/></svg>',
        '<svg xmlns="http://www.w3.org/2000/svg"><clipPath id="a"><use href="#b"/></clipPath></svg>',
        '<!DOCTYPE svg [<!ENTITY x "y">]><svg xmlns="http://www.w3.org/2000/svg"/>',
        "<svg",
    ],
)
def test_unsafe_svg_is_detected(content: str, tmp_path: Path) -> None:
    path = tmp_path / "icon.svg"
    path.write_text(content)
    assert catalog_checks.svg_problems(path)


def test_internal_clip_path_is_allowed(tmp_path: Path) -> None:
    path = tmp_path / "icon.svg"
    path.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 72 72"><desc>Made with a tool</desc>'
        '<defs><clipPath id="a"><rect width="72" height="72" fill="#fff" fill-opacity="0"/>'
        '</clipPath></defs><g clip-path="url(#a)" fill-rule="evenodd"><path d="M0 0" fill="#fff"/>'
        "</g></svg>"
    )
    assert catalog_checks.svg_problems(path) == []


def test_bundled_svgs_are_safe_and_eight_concepts_stay_distinct() -> None:
    for asset in catalog().manifest.assets:
        assert asset.derived.svg is not None
        assert catalog_checks.svg_problems(PACKAGE / asset.derived.svg.path) == []
    assets = [item for item in catalog().manifest.assets if item.pack == "drawio-network-2018"]
    assert {asset.concept for asset in assets} == catalog_checks.REQUIRED_CONCEPTS
    by_id = {asset.id: asset for asset in assets}
    # The requirement's pairs must not collapse into one symbol.
    assert by_id["onprem-nas"].symbols != by_id["onprem-san"].symbols
    assert by_id["onprem-hypervisor"].symbols != by_id["onprem-vm"].symbols
    digests = [asset.derived.png.sha256 for asset in assets]
    assert len(set(digests)) == len(digests)
    # Monitoring keeps its server symbol: a hardware display would imply something else.
    assert by_id["onprem-monitoring"].symbols == ("mxgraph.networks.server",)
    assert by_id["onprem-monitoring"].required_label == "Monitoring"
    assert set(by_id["onprem-identity-service"].symbols) == {
        "mxgraph.networks.server",
        "mxgraph.networks.users",
    }


def test_catalog_records_use_only_their_required_label() -> None:
    for record in catalog().records.values():
        if record.representation.kind == "custom_asset":
            asset = catalog().assets[str(record.representation.asset)]
            assert str(record.representation.label).startswith(asset.required_label)


def test_every_cited_page_has_a_recorded_check() -> None:
    errors: list[str] = []
    assert catalog_checks.check_source_evidence(catalog(), errors) >= 100
    assert errors == []
    evidence = json.loads((ROOT / catalog_checks.SOURCE_CHECKS).read_text())
    for page in evidence["pages"]:
        assert page["http_status"] == 200
        assert all(claim["matched"] for claim in page.get("claims", []))


def test_an_unchecked_source_fails(tmp_path: Path) -> None:
    (tmp_path / catalog_checks.SOURCE_CHECKS).parent.mkdir(parents=True)
    (tmp_path / catalog_checks.SOURCE_CHECKS).write_text('{"pages": []}')
    errors: list[str] = []
    for document in catalog_checks.DOCUMENTS.values():
        target = tmp_path / document
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / document, target)
    catalog_checks.check_source_evidence(catalog(), errors, tmp_path)
    assert any("no recorded source check" in error for error in errors)


def test_bad_document_reference_fails() -> None:
    errors: list[str] = []
    catalog_checks.check_source("doc:requirements#no-such-anchor", "x", errors)
    catalog_checks.check_source("doc:nowhere#x", "x", errors)
    catalog_checks.check_source("http://example.invalid", "x", errors)
    assert len(errors) == 3


def test_plugin_tree_holds_no_assets_outside_the_checked_package() -> None:
    errors: list[str] = []
    catalog_checks.check_plugin(errors)
    assert errors == []
    output = subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "plugins"],
        cwd=ROOT,
        text=True,
    )
    assert not [
        name
        for name in output.splitlines()
        if Path(name).suffix.lower() in catalog_checks.ASSET_SUFFIXES
    ]


def test_catalog_discovery_is_bounded_and_filterable() -> None:
    result = catalog().search(limit=10_000)
    assert result["returned"] == min(len(catalog().records), MAX_RESULTS)
    assert result["total"] == len(catalog().records)
    aws = catalog().search(provider="aws", entity="resource", query="load balancer")
    assert [item["id"] for item in aws["records"]] == [  # type: ignore[attr-defined]
        "aws.network.application_load_balancer"
    ]
    assert catalog().search(type_id="aws.compute.ec2")["total"] == 1
    assert catalog().search(query="ECS", provider="aws")["total"] == 0
    kubernetes = catalog().search(kubernetes=True, provider="onprem")["total"]
    assert isinstance(kubernetes, int) and kubernetes > 22
    assert catalog().search(limit=1)["truncated"] is True


def test_cli_catalog_and_capabilities_report_the_blocker(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(sys, "argv", ["cloud-diagrams", "catalog", "--type", "huawei.compute.ecs"])
    assert cli.main() == 0
    record = json.loads(capsys.readouterr().out)["records"][0]
    assert record["representation"]["asset"] == "huawei-ecs"
    assert record["status"] == "private_use_only"
    monkeypatch.setattr(sys, "argv", ["cloud-diagrams", "catalog", "--taxonomy-list"])
    assert cli.main() == 0
    assert len(json.loads(capsys.readouterr().out)["taxonomy"]) == len(catalog().taxonomy_ids)
    monkeypatch.setattr(sys, "argv", ["cloud-diagrams", "capabilities"])
    assert cli.main() == 0
    report = json.loads(capsys.readouterr().out)
    assert [item["id"] for item in report["release_blockers"]] == ["O-002"]
    assert report["render_available"] is False
