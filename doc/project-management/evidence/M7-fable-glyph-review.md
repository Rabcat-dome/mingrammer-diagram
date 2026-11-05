# Review of 3835439 — Refuse labels the bundled fonts cannot draw (D-034)

Reviewer: Claude (model name as given to me: Fable 5.1, `claude-fable-5-1`), independent, no prior context.
Range: `git diff a4bf065 3835439` on `codex/label-glyphs`. Date: 2026-11-05.
Scratch output: `reports/fable-glyph-work/` (git-ignored). Nothing published. No tracked file edited; mutation runs were restored from backups and `git status` is clean.

## Disposition

**Approved.** No P1 or P2. Five P3 notes below, three of them wording in docs or tests, two of them test gaps. The parser is right, the check sees everything the drawing code emits, the refusal leaves nothing on disk, the exit code is 2 through the plugin binary, and no label text reaches a diagnostic.

## What I ran

- `uv run --frozen python -m pytest -q tests/test_render_smoke.py tests/test_render_security.py tests/test_work_plugin.py` — all passed (636 tests).
- `reports/fable-glyph-work/compare_cmap.py` under `uv run --no-project --with fonttools` — compares `font_characters` with fontTools for every code point of every Unicode subtable in both fonts.
- `reports/fable-glyph-work/probe_engine.py` — 23 labels through the real engine, some with `undrawable_text` monkeypatched out to see what Graphviz draws for a refused character; PNGs saved under `reports/fable-glyph-work/probe/`.
- The plugin binary `plugins/cloud-architecture-diagrams/bin/cloud-diagrams render` with a throwaway `XDG_DATA_HOME`, on a model whose title holds `✓` and whose resource name holds `→` beside a marker word, and on a model with Cyrillic and Greek text.
- Five mutations of `checks.py` / `icons.py` against the new tests (restored afterwards).

## Not run

`scripts/reproduce_core.py`, `scripts/quality_gate.py` (as instructed), the visual-regression lane, the Work plugin build, any second machine, and the M7 evidence claim that a headless Sonnet session exercised the fix. I did not verify the fontTools version number `4.60.1` quoted in the test comment; the counts it gives are what fontTools 4.6x reports here.

## 1. Font table parser (`src/cloud_architecture_diagrams/render/icons.py:131-179`)

Correct for both formats on both fonts.

- Noto Sans: four Unicode subtables, (0,3) and (3,1) format 4 with 2877 entries, (0,4) and (3,10) format 12 with 2965 entries. Parser result: 2965 code points, equal set to fontTools `getBestCmap()` and to the union of all Unicode subtables. No code point maps to glyph 0.
- Noto Sans Thai: two format 4 subtables, 101 entries. Parser: 101, equal set. No code point maps to glyph 0.
- Format 4 arithmetic checked against the spec: column offsets (`endCode` at +14, `startCode` at +16+2n, `idDelta` at +16+4n, `idRangeOffset` at +16+6n), the `&idRangeOffset[i] + idRangeOffset[i] + 2*(c-start)` address, the "array glyph 0 means missing, before the delta" rule, and the terminal `0xFFFF` segment (correctly excluded, as the test asserts). Format 12: `numGroups` at +12, 12-byte groups at +16, `startGlyphID` 0 excluding only the first code point of the group.
- Because the real fonts never map to glyph 0, both glyph-0 branches are exercised only by the synthetic font in `test_a_character_mapped_to_the_empty_box_counts_as_absent`, and that one is format 4 only (see P3-4).

## 2. Does `undrawable_text` see everything drawn? (`render/checks.py:50-70`)

Yes. I traced every string `render/draw.py` passes to `literal(...)`: the root label (`title_lines` + `notice_lines`), each cluster label (`group.lines`), each node label (`node.lines`, which already include the service label, membership notes, Kubernetes property and reference notes, and the generic-fallback lines), each edge label (`edge.lines`), the legend title `"Legend"` and the legend sample labels (the edge `kind` names, a closed ASCII table), and the `DRAFT:` and provider-box lines (ASCII literals). Anchor and legend point nodes have empty labels. Nothing reaches the image outside those five tuples.

False refusals and false passes, by probe:

| Label | In table? | Check | Engine really draws |
|---|---|---|---|
| `a` U+0301 `b` (combining acute) | yes | passes | `áb`, correct |
| `a` U+0E48 `b` (Thai tone mark on Latin base) | yes | passes | mark over `a`, no box |
| U+0E01 U+200B U+0E02 | yes | passes | correct, ZWSP invisible |
| `x` U+2060 `y`, `a` U+00AD `b`, `a` U+200E `b` | yes | passes | identical PNG to `xy` / `ab` |
| `a` U+00A0 `b`, `a  b` | yes | passes | correct |
| U+0E17 U+0E35 U+0E48, U+0E46, U+0E3F | yes | passes | correct |
| `a` U+FE0F `b`, `a` U+FE0E `b` (bypassed) | **no** | **refused** | **PNG byte-identical to `ab`** — no box (P3-1) |
| `1` U+20E3 (bypassed) | no | refused | hex box, as claimed |
| `a` U+E000 `b` (bypassed) | no | refused | hex box |
| `a` U+FFFE `b` (bypassed) | no | refused | `RENDER_SVG_UNSAFE` still catches it as a second line of defence |
| `a` U+2028 `b` | yes | passes | **drawn as a line break** (P3-5, pre-existing) |
| `a` TAB `b`, `a` U+000B `b` | — | `SCHEMA_FIELD_INVALID` | never reaches render |

Characters only in Noto Sans Thai (all of U+0E01–U+0E5B) draw through fontconfig fallback; characters in both (`-`, U+2010, U+25CC, U+0303, U+0331, the zero-width set) draw with either.

## 3. Disk, exit code, diagnostics

Through `plugins/cloud-architecture-diagrams/bin/cloud-diagrams render --output <dir>` with a title holding `✓ secretword` and a resource name `secretlabel → right`: exit **2**, stdout is the JSON result with two `RENDER_TEXT_UNDRAWABLE` errors (`/title`, `entity_id` null; `/labels`, `entity_id` `app`), messages end `Found U+2713.` / `Found U+2192.`, stderr empty, `<dir>` **not created**. `grep` for the marker words, `→` and `✓` across stdout and stderr: zero hits. The check runs before `OutputRoot(output)` and before `find_engine()` (`render/__init__.py:328-331`), so a host without Graphviz also gets this refusal first, which is the right order. `exit_status` maps the code to 2 because it is in `REQUEST_CODES` (`errors.py:122`); the Work adapter maps core exit 2 to `validation_failed` (`work_adapter/tools.py:399`), which is what `test_work_plugin.py:1520` expects, and that test passes against the symlinked `src`.

## 4. Do the new tests fail for the reasons their names give?

| Mutation | Result |
|---|---|
| `undrawable_text` returns `[]` | 33 failures: every `..._is_refused`, `..._named_at_once`, `..._stays_short`, and `test_text_xml_cannot_hold_never_reaches_the_engine` |
| Format 4: do not skip array glyph 0 before the delta | `test_a_character_mapped_to_the_empty_box_counts_as_absent` fails, as named |
| Format 12: do not skip a group starting at glyph 0 | **no failure** (P3-4) |
| Drop `/notices` from the drawn list | **no failure** (P3-4) |
| Format 4: apply no delta to array glyphs | no failure, but presence is unchanged unless `glyph+delta ≡ 0 mod 2^16`, so this is not a real gap |

`test_a_font_character_list_comes_from_the_font_itself` asserts the exact counts fontTools gives (2965, 101), so a parser regression on the real fonts would surface there. `test_every_catalog_text_can_be_drawn` passes and covers the attribution strings that become `/notices`.

## 5. Statements elsewhere

- `doc/design/core-contract.md:21` and `:155`, `decisions.md` D-034, `HANDOFF.md:47`, `M7-claude-plugin.md`: consistent with the code. The `RENDER_SVG_UNSAFE` remedy rewording ("Report this as a renderer defect") is truthful: the only font-held code point XML cannot hold is U+0000, which the schema already refuses as a control character, so model text can no longer reach that check.
- `model-guide.md:22` (identical in both plugins): the examples `–`, `—`, `…`, `>`, `>=` are verified drawable by `test_english_thai_and_common_punctuation_still_draw`; one overbroad phrase, see P3-2.
- `core-contract.md:3` still says the package is `0.5.0a1`, see P3-3.
- `pyproject.toml`, `__init__.py`, `uv.lock`, `plugins/cloud-architecture-diagrams/pyproject.toml` (symlink target) all say `0.5.0a2`. `plugins/cloud-architecture-work/plugin.json` stays `0.1.0-alpha.1`, which HANDOFF:47 correctly says changes at the next build.

## Findings

**P3-1 — The refusal message and a test claim a box for characters that draw as nothing.**
`src/cloud_architecture_diagrams/render/errors.py:23` ("which would draw as an empty box"), `doc/design/core-contract.md:155`, and `tests/test_render_smoke.py:1113` (U+FE0F listed under "seen or likely in labels are refused"). Input: resource name `a️b` with the check bypassed. Observed: the PNG is byte-identical to the PNG for `ab` (SHA-256 prefix `bc318d4426`); same for U+FE0E. Pango hides Default_Ignorable code points a font lacks, so VS15/VS16, U+061C, U+180B–180E, the U+E0100–E01EF selectors and the tag characters are refused though they would draw correctly. Harmless in practice (a stray VS16 almost always rides on an emoji that is refused anyway), but the message and the test's premise are not true for these. Either exempt `Default_Ignorable_Code_Point` characters from the check, or reword the message and the test name to say "not in the bundled fonts" rather than "would draw as a box".

**P3-2 — Guide overstates what is refused.**
`plugins/cloud-architecture-diagrams/skills/architecture-model/references/model-guide.md:22` and the Work copy: "`render` refuses `→`, `✓`, `≥`, emoji and other scripts". Input: resource name `Сервер Ελλάδα` through the plugin binary. Observed: exit 0, bundle rendered. Noto Sans holds Latin, Greek and Cyrillic, so "other scripts" should read "CJK, Japanese, Korean and other scripts the fonts lack" or similar, otherwise an agent will needlessly rewrite Greek or Cyrillic.

**P3-3 — Contract header still names the old version.**
`doc/design/core-contract.md:3`: "Package `0.5.0a1` is a core development version", while `:21`, `:155`, `pyproject.toml:7` and `__init__.py:3` say `0.5.0a2`. Present-tense statement now untrue. (`HANDOFF.md:33` also says "Core is `0.5.0a1`", but inside the dated S08 record, which `:47` then supersedes; acceptable as history.)

**P3-4 — Two untested paths.**
`src/cloud_architecture_diagrams/render/icons.py:156` (format 12 group whose `startGlyphID` is 0) and `render/checks.py:54` (`/notices` field): deleting either leaves all tests green. Both are verified correct by inspection and, for format 12, by the exact fontTools match; the synthetic-font test could add a format 12 subtable with a glyph-0 group, and one test could put an absent character into an attribution string through a monkeypatched catalog to pin `/notices`.

**P3-5 — Pre-existing, surfaced by this review: U+2028/U+2029 pass the schema and draw as a line break.**
`model-guide.md:22` says "no control characters, so no newlines". Input: resource name `a b`. Observed: schema accepts it (category Zl, not Cc), the table holds it (Noto Sans maps it to an empty glyph), the check passes it, and the PNG shows `a` and `b` on two lines (`reports/fable-glyph-work/probe/line_sep.png`). Not caused by this change, and `check_content` still passes, but the guide's claim is untrue and a label can smuggle a line break. Worth a schema rule alongside the control-character one.

## Rating summary

| # | Rating | Where |
|---|---|---|
| 1 | P3 | `render/errors.py:23`, `core-contract.md:155`, `tests/test_render_smoke.py:1113` |
| 2 | P3 | both `model-guide.md:22` |
| 3 | P3 | `core-contract.md:3` |
| 4 | P3 | `render/icons.py:156`, `render/checks.py:54` (test gaps) |
| 5 | P3 | `model-guide.md:22`, `models.py` text rule (pre-existing) |

Disposition: **approved**.

## Disposition of these findings

Recorded by the implementer, Claude Opus 5.5. The reviewer ran as Claude Fable 5.1 / Medium in a fresh agent under D-021, and it shares a vendor with the implementer.

| Finding | Disposition |
|---|---|
| P3-1 | Fixed. The message, the check's comment and the contract now say the character can draw as a box. Variation selectors stay refused, because a session can simply drop one |
| P3-2 | Fixed. The guide names scripts the fonts lack, such as Chinese, Japanese and Korean |
| P3-3 | Fixed |
| P3-4 | Fixed. New tests cover a format 12 run starting at glyph 0, and the `/notices` row |
| P3-5 | Open. It predates this change, and a schema rule is a change of its own |

The table in section 2 gives two Thai labels as code points, because repository documents stay English. No independent review covers these fixes, which are wording and two tests, plus one word in a diagnostic's message.
