# S02 Follow-up — User-Supplied Huawei Pack and draw.io On-Premises Symbols

Checked: 2026-10-31 | Status: Source assessment and eight concept mappings complete; asset export/visual/package checks remain M2/M4 work.

**S06 correction:** `bc0ccab15cb08e8e03491aa14a30eb2801caaf81`, called a commit below, is the annotated tag object for v29.3.2. The commit is `48b181339578e11da7052ebf5b1fba8499418b77`, and the audited blobs are unchanged. See the [S06 record](S06-provider-catalogs.md#on-premises-representations).

This supplements the [initial S02 assessment](S02-icon-sources-and-rights.md). Product authority remains [requirements revision 0.5](../../requirements/requirements.md). The user supplied a Huawei repository and requested draw.io-type symbols for the eight on-premises gaps. Detailed [supplemental metadata](S02-supplemental-icons.json) records audited sources and mappings; it contains no artwork or executable code.

## 1. Huawei repository assessment

Source: [JuanDiaz00/Huawei-Cloud-draw.io-icons](https://github.com/JuanDiaz00/Huawei-Cloud-draw.io-icons), commit `ea52d7356e172a85cde7538f293a663eb137611d` (2025-08-13).

- The [pinned README](https://github.com/JuanDiaz00/Huawei-Cloud-draw.io-icons/blob/ea52d7356e172a85cde7538f293a663eb137611d/README.md) identifies VeryIcon as its source and explains scratchpad import. It is a community repack, not established here as a Huawei-published asset library.
- `HuaweiCloud Icons.xml` is a valid mxlibrary containing **155 PNG entries**. Its Git blob is `0bd260648d2525e86c87c671ea9f9deb8d825a14`; the raw XML SHA-256 is `1afc1f2a0fda735c7b9eda88466725b720045493e61a04d392467596b8c976cd`.
- Entry display dimensions are 256x256 for 154 entries and 512x512 for one. These are library metadata, not a visual/pixel-quality certification. The XML has no SVG entries.
- Seven minimum items have unambiguous names: ECS, ELB, EIP, VPC, RDS, IAM and VPN. The other ten need alias/image verification or a different source; filenames such as `storage-55` and `other-cluster-computing-platform-services` must not be silently interpreted as OBS or CCE.
- No repository license/notice file was found in the complete tree, and GitHub license metadata is null. The linked [VeryIcon ECS page](https://www.veryicon.com/icons/miscellaneous/huawei-cloud-service-icon/computing-ecs.html) attributes the pack to AIyangyang and states that personal/commercial use is free. That is evidence of a usage claim; the audited page does not explicitly establish plugin redistribution of the source assets or original Huawei authorization.

**Disposition:** technically usable as a PNG source candidate for verified services. Keep it as an alternative; do not replace the LATAM color/SVG candidate by default. The LATAM inventory has clearer mappings for all 17 minimum items and a vector source path, although its redistribution evidence is also unresolved. Neither source is cleared for bundling by this assessment. Existing O-002 remains open; the new link does not by itself resolve it.

The connector returned empty content for the >1 MB XML and rejected its raw fetch. The file was then read through the pinned public raw URL using system curl after local Python's certificate verification failed. TLS verification was retained, input size was bounded and the Git blob hash was checked before parsing. No upstream script was executed or image saved.

## 2. draw.io-type symbols for the eight on-premises gaps

Yes: use the generic Network 2018 vocabulary, with labels/composition where there is no dedicated semantic icon. This resolves symbol-direction selection for the eight concepts; it does not claim eight native specialist icons or completed artwork exports.

| Concept | Verified source symbol IDs | Planned representation |
|---|---|---|
| Load balancer | `mxgraph.networks.load_balancer` | Direct generic load-balancer symbol |
| Hypervisor | `mxgraph.networks.server` + `mxgraph.networks.virtual_server` | Labeled hypervisor host/composition; distinguish host from guest VM |
| VM | `mxgraph.networks.virtual_server` | Virtual-server symbol labeled VM |
| NAS | `mxgraph.networks.nas_filer` | Direct NAS filer symbol |
| SAN | `mxgraph.networks.storage` | Storage symbol labeled SAN, with the declared block/fabric relationships |
| Identity service | `mxgraph.networks.server` + `mxgraph.networks.users` | Labeled identity-service composition; no implied AD/Dex/other product |
| Backup system | `mxgraph.networks.server_storage` | Labeled backup service/repository; use tape imagery only when tape is stated |
| Monitoring | `mxgraph.networks.server` + explicit Monitoring label | Observability service/component; do not use a hardware display alone to imply monitoring |

Seven distinct source symbols support these eight concept mappings. Their names exist in the actual stencil XML and the sidebar definitions. Ownership, device role, traffic, storage and monitoring relationships still come from the canonical model.

## 3. Source versions and asset conditions

Audited current draw.io commit: `3e707fd20b6930778d6f6bf6e4d0079b4bce366b` (2026-10-30). The [README](https://github.com/jgraph/drawio/blob/3e707fd20b6930778d6f6bf6e4d0079b4bce366b/README.md) and [stencil conditions](https://github.com/jgraph/drawio/blob/3e707fd20b6930778d6f6bf6e4d0079b4bce366b/src/main/webapp/stencils/LICENSE) distinguish application code from icon/stencil assets and restrict asset use in the Atlassian ecosystem. They separately address generated end-user diagrams. Do not call every icon Apache-2.0 based on the code license.

A reproducible XML source candidate is available in **v29.3.2**, commit `bc0ccab15cb08e8e03491aa14a30eb2801caaf81`:

- [Generic networks.xml](https://github.com/jgraph/drawio/blob/bc0ccab15cb08e8e03491aa14a30eb2801caaf81/src/main/webapp/stencils/networks.xml), Git blob `24191cc4ab46ce2bc2c3896b811f2afd9ade43cf`, contains 57 named shapes including the seven selected symbols.
- [Sidebar-Network.js](https://github.com/jgraph/drawio/blob/bc0ccab15cb08e8e03491aa14a30eb2801caaf81/src/main/webapp/js/diagramly/sidebar/Sidebar-Network.js), Git blob `b1794fc27e33b48121cfc46680e1188722ec9bd0`, verifies the shape IDs/palette names. The audited current sidebar has the same blob.
- That snapshot's [README](https://github.com/jgraph/drawio/blob/bc0ccab15cb08e8e03491aa14a30eb2801caaf81/README.md) declares CC-BY-4.0 for JGraph-provided icons, with qualifications for third-party originals. Its [stencil LICENSE](https://github.com/jgraph/drawio/blob/bc0ccab15cb08e8e03491aa14a30eb2801caaf81/src/main/webapp/stencils/LICENSE) **already includes an Atlassian ecosystem restriction**; the older version is not an unrestricted-license workaround.

The present product targets ChatGPT Work and later Claude Code, with no Atlassian distribution in scope. M2 records the selected source's complete applicable conditions/attribution and checks asset provenance before bundling. Prefer this neutral generic family over unrelated branded Cisco/VMware/vendor shapes. This is not blanket clearance for all libraries or later distribution targets.

## 4. Integration plan and next work

- D-010 records the user's draw.io-type on-premises preference; M2-04 selects the seven symbols/compositions and retains attribution/source metadata.
- Export or convert the approved subset to bounded local SVG/PNG during asset preparation, with original/derived SHA-256 values and visual inspection. The final runtime remains diagrams/Graphviz; installing draw.io is not a new user runtime requirement.
- Treat stencil XML and sidebar JavaScript as audited build-source references, not runtime instructions or arbitrary executable inputs. No source code was run during this assessment.
- T-005/T-015/T-016 cover type distinction, packaging/attribution and visual fit. Keep eight mapped concepts distinct even when source geometry is shared.
- Huawei O-002 still needs source-asset permission evidence. S03 repository/runner work can proceed independently.

No source icons/stencils are bundled yet. The initial inventory's eight `neutral_symbol_gap` rows are historical research findings; these mappings supersede their unresolved symbol-choice status. Actual asset files, conversion, rendering and final package checks remain pending.

Validation passed: 12 English Markdown files, two JSON inventories, 54 local links/anchors, 64 requirement IDs, 17 acceptance scenarios, 32 task IDs and 31 decision/proposal/question IDs. The supplemental inventory has 155 PNG entries, seven verified title/index matches plus ten unresolved minimum items, and eight on-premises mappings using seven source symbol IDs. JSON parsing, checked links/IDs, code fences, English-only text, whitespace and absence of raw artwork passed. No icon export, runtime render or package-rights clearance is claimed.
