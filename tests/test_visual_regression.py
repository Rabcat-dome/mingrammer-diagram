"""M4-04 visual-regression lane: no change to a reference view passes without a reviewed baseline."""

import json
import shutil
from difflib import unified_diff
from pathlib import Path
from typing import Any

import pytest
from render_helpers import ROOT
from visual_helpers import (
    BASELINES,
    RECORD,
    compare_images,
    decode_png,
    digest,
    encode_png,
    engine_version,
    graph_text,
    reference_views,
    render_view,
    view_key,
)

OUTPUT = ROOT / "reports/visual-regression"
UPDATE = "uv run --frozen python scripts/update_visual_baselines.py --reason '...'"
VIEWS = reference_views()


@pytest.fixture(scope="session")
def record() -> dict[str, Any]:
    value: dict[str, Any] = json.loads(RECORD.read_text())
    return value


@pytest.fixture(scope="session")
def rendered() -> dict[str, dict[str, Any]]:
    shutil.rmtree(OUTPUT, ignore_errors=True)
    OUTPUT.mkdir(parents=True, mode=0o700)
    return {view_key(*item): render_view(*item, OUTPUT / "bundles") for item in VIEWS}


def test_the_reference_set_is_the_one_the_milestone_needs() -> None:
    assert {scenario for scenario, _ in VIEWS} == {
        "aws-three-tier",
        "azure-hub-spoke",
        "gcp-shared-vpc",
        "huawei-web",
        "onprem-physical-logical",
        "hybrid-five",
    }


def test_every_view_has_a_baseline_and_no_baseline_is_left_over(record: dict[str, Any]) -> None:
    expected = {view_key(*item) for item in VIEWS}
    assert set(record["views"]) == expected
    on_disk = {path.name.removesuffix(".graph.json") for path in BASELINES.glob("*.graph.json")}
    assert on_disk == expected
    assert {path.stem for path in BASELINES.glob("*.png")} == expected


def test_a_baseline_says_why_it_was_accepted(record: dict[str, Any]) -> None:
    assert record["reason"].strip() and record["accepted_on"]


@pytest.mark.parametrize("key", [view_key(*item) for item in VIEWS])
def test_the_normalized_graph_matches_its_baseline(
    rendered: dict[str, dict[str, Any]], key: str
) -> None:
    # This is host-independent, so unlike the image it must hold on every machine.
    current = graph_text(rendered[key]["graph"])
    baseline = (BASELINES / f"{key}.graph.json").read_text()
    changes = list(
        unified_diff(baseline.splitlines(), current.splitlines(), "baseline", "current", n=1)
    )
    assert not changes, f"{key} changed. Review it, then run {UPDATE}\n" + "\n".join(changes[:60])


def test_the_engine_is_the_one_the_baseline_was_accepted_on(record: dict[str, Any]) -> None:
    # Images are not promised byte-identical across builds (NFR-001), so name the cause directly.
    assert engine_version() == record["engine"]


@pytest.mark.parametrize("key", [view_key(*item) for item in VIEWS])
def test_the_image_matches_its_baseline(
    rendered: dict[str, dict[str, Any]], record: dict[str, Any], key: str
) -> None:
    current = rendered[key]
    baseline = (BASELINES / f"{key}.png").read_bytes()
    expected = record["views"][key]
    assert digest(baseline) == expected["png"], f"{key}: the baseline file was changed by hand"
    if digest(current["png"]) == expected["png"] and digest(current["svg"]) == expected["svg"]:
        return
    share, marked = compare_images(baseline, current["png"])
    (OUTPUT / f"{key}.before.png").write_bytes(baseline)
    (OUTPUT / f"{key}.after.png").write_bytes(current["png"])
    if marked is not None:
        (OUTPUT / f"{key}.diff.png").write_bytes(marked)
    changed = "not computed" if share is None else f"{share:.4%} of pixels"
    pytest.fail(f"{key} changed: {changed}. See {OUTPUT}, review it, then run {UPDATE}")


def small_image() -> bytes:
    rows = [bytes([index % 255, 40, 80, 255]) * 6 for index in range(5)]
    return encode_png(6, 5, 4, rows)


def test_the_comparison_finds_one_changed_pixel_and_marks_it() -> None:
    before = small_image()
    width, height, channels, rows = decode_png(before)
    rows[2] = rows[2][:4] + b"\x09\x09\x09\xff" + rows[2][8:]
    after = encode_png(width, height, channels, rows)
    share, marked = compare_images(before, after)
    assert share == pytest.approx(1 / 30)
    assert marked is not None
    marked_rows = decode_png(marked)[3]
    assert marked_rows[2][4:8] == b"\xff\x00\x00\xff"
    assert marked_rows[1][4:8] != b"\xff\x00\x00\xff"


def test_identical_images_compare_as_unchanged() -> None:
    assert compare_images(small_image(), small_image()) == (0.0, None)


def test_a_different_size_counts_as_a_whole_change() -> None:
    other = encode_png(6, 4, 4, [bytes([1, 2, 3, 255]) * 6] * 4)
    assert compare_images(small_image(), other) == (1.0, None)


@pytest.mark.parametrize("filter_type", [0, 1, 2, 3, 4])
def test_the_decoder_reads_every_png_filter(filter_type: int) -> None:
    # Cairo chooses filters per row, so each must decode or the diff would mark the wrong pixels.
    import struct
    import zlib

    rows = [bytes([10, 20, 30, 255, 40, 50, 60, 255]), bytes([70, 80, 90, 255, 11, 22, 33, 255])]

    def filtered(row: bytes, above: bytes) -> bytes:
        out = bytearray()
        for index, value in enumerate(row):
            left = row[index - 4] if index >= 4 else 0
            up = above[index]
            corner = above[index - 4] if index >= 4 else 0
            estimate = left + up - corner
            near = [abs(estimate - left), abs(estimate - up), abs(estimate - corner)]
            paeth = (left, up, corner)[near.index(min(near))]
            predicted = (0, left, up, (left + up) // 2, paeth)[filter_type]
            out.append((value - predicted) & 255)
        return bytes(out)

    raw = bytes([filter_type]) + filtered(rows[0], bytes(8))
    raw += bytes([filter_type]) + filtered(rows[1], rows[0])

    def chunk(kind: bytes, body: bytes) -> bytes:
        return (
            struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body))
        )

    data = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", 2, 2, 8, 6, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw))
        + chunk(b"IEND", b"")
    )
    assert decode_png(data) == (2, 2, 4, rows)


def test_a_path_inside_the_reports_folder_stays_ignored_by_git() -> None:
    # Bundles here can hold private-use icons, as render-smoke's do.
    assert "reports" in Path(ROOT / ".gitignore").read_text()
