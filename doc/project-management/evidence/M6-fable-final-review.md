# M6-03 final independent release review at e167deb

**Disposition: approved for tagging, as a private personal release.** No P1 or P2 finding. Four P3 findings, none of which blocks a private personal release. No Critical, High or unjustified Medium finding remains open across the evidence records, in M6's terms; the one Medium that remains, the Huawei preview reaching the chat host, has the owner's disposition in D-026.

- Reviewer: Claude Fable 5.1 (`claude-fable-5-1`), through Claude Code, as a fresh agent with no prior context on this project. The reasoning-effort setting is not exposed to this session. Claude Opus 5.5 did the recent implementation (D-030 to D-032), so this reviewer shares a vendor with the implementer; this report is not an independent-vendor opinion, and the GPT reviews in S11 are the only other vendor's.
- Date: 2026-11-05, Asia/Bangkok.
- Commit: `e167deb79702127f516ef8d95630a2a16dc604af`, branch `main`, checkout `/Users/visarut.pha/Documents/source/easybuy/mingrammer-diagram`. The working tree was clean on entry and is clean on exit. No tracked file was edited, nothing was committed, pushed, tagged or published. No Huawei image was opened or sent anywhere; everything with Huawei icons was read as `view.json` graphs and manifests.
- Scratch: `reports/fable-final-work/` (git-ignored): `probe_step1.py`, `probe_step1b.py`, `probe_step2.py`, their render output under `out/` and `out2/`, the throwaway `home/`, the unpacked wheel and sdist under `unpack/`, the Work plugin build under `work-plugin/`, and `quality-gate.out`.

## Findings

Ranked P1, P2, P3. Each gives the file and line at `e167deb`, the input that fails, the wrong result, whether I confirmed it, and why the tests miss it. There are no P1 or P2 findings.

### P3-1. Any selected relationship between a pair hides the typed reference, whatever the relationship's kind or direction

- File: `src/cloud_architecture_diagrams/render/graph.py`, lines 254-259 (`self.linked` is built from every selected relationship, keyed by the unordered pair) and 456-461 (the note is dropped when the pair is in `linked`).
- Input: the Azure reference, `aks-namespaces` view, with `configuration-deployment-secret` left out of the view's `relationship_refs`, and a new relationship `{"id": "mgmt-dep-secret", "source_ref": "web-deployment", "target_ref": "web-secret", "kind": "management"}` added and selected. Strict validation passes (FR-029 has no endpoint rule for `management`, by D-030).
- Wrong result: `web-deployment` draws as `['web-frontend', 'Deployment', 'replicas: 2']`. The `secret: web-frontend-secret` line that appears when no edge joins the pair is gone, and the only line between the two reads as `management`, not as a configuration reference. The same happens with an `observability` edge in the other direction (`web-secret -> web-deployment`). Section 6.1 says the detail view must retain supplied configuration and security references; here the reference is neither drawn as what it is nor noted. The exported `model.json` and `view.json` memberships still carry the fact.
- Confirmed: yes, `probe_step1.py` probes A and A2.
- Why the tests miss it: `tests/test_references.py:973` (`test_a_typed_reference_stays_visible_until_a_relationship_draws_it`) removes and adds only a `configuration` edge, so it never meets an edge of another kind between the same pair. The baselines hold no such pair either.
- Severity: P3, because the model has to declare the reference and also draw a differently typed edge between the same two entities without the matching edge, which is unusual, the pair stays visibly joined, and the exported source keeps the fact. A stricter reading of 6.1 would make it P2. A fix is to key `linked` by pair and by the kinds that draw each reference (`configuration` for `config_refs` and `secret_refs`, `storage` for the volume references, `ownership` for `owner_ref`, `traffic` for `service_refs` and `target_refs`), or simply to keep the note whenever the selected edge's kind is not one of those.

### P3-2. `test_every_kind_of_typed_reference_has_a_note` does not test that any reference has a note

- File: `tests/test_references.py`, lines 1007-1024.
- What it does: asserts that the set of `KubernetesContext` fields ending in `_ref` or `_refs`, minus the four placement fields, equals a fixed set of nine names. It never imports or calls the renderer.
- Wrong result: removing the `("owner", ...)` entry, or any other, from `_typed_references` in `graph.py` leaves this test green; only a new field added to the model fails it. The P0 report lists it under FR-018 as one of the checks behind "Met", and its name says more than it checks. The same applies to the `partly`-era note in S10 about name-only tests.
- Confirmed: by reading; I did not mutate a tracked file. The test body contains no call into `cloud_architecture_diagrams.render`.
- Why the tests miss it: the other new tests (`test_a_detail_view_lists_what_the_model_declares`, lines 925-949, and `test_a_typed_reference_stays_visible...`) cover `replicas`, `labels`, `type`, `ports` and `secret_refs` only; `service`, `target`, `claim`, `volume`, `storage class`, `config`, `service account` and `owner` lines are covered by nothing except the frozen graph baselines, which detect change rather than check meaning.
- Severity: P3. The behavior is right today (the baselines show `storage class:` and `owner:` lines, and my probes show `secret:`); the finding is test strength and a slightly generous FR-018 record.

### P3-3. `build.json` records `source_dirty: true` on a clean checkout when Git's global excludes are absent

- File: `scripts/build_work_plugin.py`, lines 82-90 (`source_commit` uses `git status --porcelain`).
- Input: `python3 scripts/build_work_plugin.py --output ...` with `HOME` set to a folder that has no `~/.gitconfig` and therefore no global `core.excludesFile`. The checkout holds a local `.claude/` folder that only the global excludes ignore.
- Wrong result: `build.json` says `"source_dirty": true` for the clean commit `e167deb`. With the real `HOME` the same command says `false`, and both builds produce the same version `0.1.0-alpha.1+88ce2c0cd0dc` and the same archive digest, so the package itself is unaffected. On a second machine without that global ignore, the marker would misstate the build's source.
- Confirmed: yes, both ways, in this session.
- Why the tests miss it: the tests build under the repository's own environment, where `.claude/` is ignored; `.claude/` is not in the repository's `.gitignore`.
- Severity: P3. A record-accuracy nit. Adding `.claude/` to `.gitignore`, or ignoring untracked files in `source_commit`, removes it.

### P3-4. The T-002 and T-004 scenario texts are met by a reading the records state, not by the literal words

- T-002 says "explicit peering/VPN". The fixture `tests/fixtures/references/azure-hub-spoke.json` has an explicit `peering` edge with the label `VNet peering`, and draws the VPN Gateway as a node (`Azure VPN Gateway`), but no `vpn` relationship exists in the model, because the brief names no far end. The P0 record's owner note says exactly this and leaves the reading to the owner (D-023). The `vpn` edge kind is exercised by T-006 (`link-azure-vpn`, `Site-to-site VPN, two-way`).
- T-004 says "every required Huawei catalog item resolves with approved icon evidence". The T-004 fixture holds 12 of the 15 required Huawei items with native icons plus CCE and a Security Group; Direct Connect is absent from `huawei-web.json` and appears in `hybrid-five.json` (`huawei-direct-connect`, `custom_asset`, pack `huawei-latam-color`). Every one of the 15 resolves through the catalog check `test_required_huawei_items_are_reported_by_name` and draws through `test_all_fixture_views_draw_every_catalog_type`. The approval is D-018's private-use acceptance, which the records say plainly is not cleared rights.
- Confirmed: by reading the fixtures, mapping every view of both fixtures (`probe_step2.py`), and reading the tests.
- Severity: P3, record-reading only. No change is needed for a private release; the table below says "meets, with the recorded reading".

## 1. The unreviewed code: `4521939~6..e167deb`

What changed in `src`, `plugins`, `scripts`, `tests` and `.github`: 69 lines in `render/graph.py` (the FR-018 detail lines), one bullet in the model guide (linked into both plugins), one sentence in `build_traceability.py`, a Service type and ports added to each of the six reference fixtures, 11 regenerated Kubernetes detail baselines (graph and PNG), and new tests in `test_references.py`, `test_render_security.py` and `test_catalog_license.py`. Nothing changed under `.github`.

Own probes, all run with a throwaway `HOME` under `reports/fable-final-work/home` against the Azure reference (`probe_step1.py`, `probe_step1b.py`):

| Question | Probe | Result |
|---|---|---|
| Misstate a model | Labels `{"a": "b, c=d"}` or key `"a, c=d"` on a Deployment, which would make `labels: a=b, c=d` ambiguous | Refused: `LABEL_SYNTAX_INVALID` is an error for Kubernetes resources, so only `[a-z0-9A-Z._-]` keys and values reach the line |
| Misstate a model | Ports `[443:https/TCP, 80:8080/TCP]`, a named target port | Line `ports: 443:https/TCP, 80:8080/TCP` in the graph and in the SVG text, in model order |
| Hide a fact | A selected `management` or reverse `observability` edge between Deployment and Secret | Hides the `secret:` note: P3-1 above |
| Hide a fact | A Secret referenced by a Deployment but left out of the view | `secret: web-frontend-secret` still noted; the Secret's ID is in `VIEW_EXCLUSIONS` |
| Hide a fact | `provider` grouping on the same entities | No `replicas`, `type`, `ports`, `labels` or reference lines, as the contract says; the overview stays compact and the exported model keeps them |
| Leak | A Secret with `properties.labels` | `K8S_SECRET_REFERENCE_ONLY` error; a Secret carries only its name, and the model has no value field |
| Leak | Two Secrets with one display name | The note names them by display name, so it cannot tell them apart; names are what every other note uses too, and the exported `view.json` keeps IDs. Not counted as a finding |
| Break a limit | A Deployment with 900 `secret_refs` of 256-character names (payload 452 KB, under the 1 MiB input bound) | `RENDER_PIXEL_LIMIT`, exit 2, nothing published, remedy says to split the view; 0.8 s |
| Break a limit | 180 Secrets selected in the view with no edges (inside 200/300) | `RENDER_PIXEL_LIMIT`, bounded refusal, 2.6 s |
| Break a limit | 64 labels of maximal Kubernetes size | `RENDER_PIXEL_LIMIT`, bounded refusal, 1.3 s |
| Break a limit | 5 to 50 references and 5 to 30 labels of realistic size | Every size renders at `scale: 1.0`; the tallest node reaches 75 lines and 3,453 px, inside the limits |
| Order | `secret_refs` listed in two orders | The line follows the model's order, deterministically; labels are sorted by key, as the test says |
| Order | View `relationship_refs` order | `linked` is a set of pairs, so order cannot matter |

The refusals above are the existing NFR-009 bounds working on the new lines; they open no new class, because membership notes already amplified labels the same way (`amplified_model` in `tests/render_helpers.py`). The new lines do lower the size at which a detail view with many references hits the pixel limit; a model would need hundreds of references on one node to reach it.

Other typed references or properties that should appear and do not: none that section 6.1 names. The nine `KubernetesContext` references and the four `Properties` fields are all drawn in detail views; `cluster_ref`, `namespace_ref`, `node_pool_ref` and `node_ref` are memberships and already note or nest. `Properties` on a non-Kubernetes resource (for example AWS tags in `labels`) draw in no view, and no requirement asks for that.

Do the new tests fail for the reason their names give:

- `test_a_detail_view_lists_what_the_model_declares`, `test_a_workload_scaled_to_zero_still_says_so`, `test_an_overview_stays_compact`, `test_labels_read_the_same_whatever_order_a_model_lists_them_in`: yes, each asserts the drawn lines.
- `test_a_typed_reference_stays_visible_until_a_relationship_draws_it`: yes for a `configuration` edge; see P3-1 for what it does not reach.
- `test_every_kind_of_typed_reference_has_a_note`: no, see P3-2.
- `test_every_host_fixture_holds_every_kubernetes_kind`: yes; it reads the five fixtures against `KubernetesKind`.
- `test_the_onprem_pack_terms_reach_the_bundle_and_the_notice`: yes; it reads the pack's conditions from a real bundle's manifest and from `NOTICE.md`.
- `test_the_limits_stay_the_ones_the_measurements_set`: yes; the eleven numbers equal `limits.py`, and the contract's table (`core-contract.md` lines 117-126) states the same ones.
- `test_a_diagrams_version_other_than_the_lock_blocks_the_render`: yes; `render/icons.py:70` compares the lock to `metadata.version("diagrams")` in the calling process, before any import, and the test sees `RENDER_ASSET_UNSAFE` with an empty output tree. The code is shared with other asset refusals, so the test proves a refusal, not the reason in words.
- `test_a_diagrams_version_other_than_the_lock_fails_the_lane`: yes; it asserts the lane's own message.

## 2. The six reference scenarios

Checked by reading each requirement row and S01 brief against the fixture, the tests in `tests/test_references.py`, and my own mapping of every view of the AWS, Azure, Huawei and hybrid fixtures through the real renderer (`probe_step2.py`, graphs and manifests only).

| Scenario | Requirement text | Fixture and what I saw | Tests | Verdict |
|---|---|---|---|---|
| T-001 AWS three-tier | SVG/PNG; valid subnet/AZ mapping; multi-subnet ALB verified against its product rules; requested security/monitoring retained | `aws-three-tier.json`: one `alb` with `subnet: [subnet-public-a, subnet-public-b]` in two AZs, `security: [sg-alb]`; three security groups drawn as groups and noted on each member; NAT, IGW, CloudWatch, S3, RDS present; four views render at `scale: 1.0`. The ALB record's rules are `min_subnets: 2, min_subnet_zones: 2, max_networks: 1`, with negative cases `aws-alb-one-subnet`, `aws-alb-subnets-same-zone`, `aws-alb-single-zone` in `tests/fixtures/semantics/cases.json` | `test_t001_*` (4), `test_negative_case_fails_with_its_code` | Meets its text |
| T-002 Azure hub/spoke | Ownership vs attachment preserved; explicit peering/VPN; supplied firewall/NSG shown | `azure-hub-spoke.json`: `overview` nests `spoke-vm` by subnet with no resource-group boxes; `ownership` nests by `rg-spoke > subscription > tenant` and notes `network: vnet-spoke`; one undirected `peering` edge labeled `VNet peering` is the only hub-spoke crossing; `hub-firewall`, `hub-vpn-gateway`, `nsg-spoke` and the NIC `attachment` edge are drawn. No `vpn` edge: see P3-4 | `test_t002_*` (5) | Meets its text, with the recorded reading of "VPN" as the drawn gateway (owner note, D-023) |
| T-003 GCP Shared VPC | Global network/regional subnets; host/service-project references; workload placement validated | `gcp-shared-vpc.json`: `vpc-shared` has no parent; subnets `located_in` two regions; `projects` view nests `vm-web-a` under `project-app-service`, the VPC under `project-network-host`, with a `shared-vpc-attachment` edge; moving a workload to the wrong subnet gives `PLACEMENT_REGION_MISMATCH` | `test_t003_*` (4), `test_scope_and_network_dimensions_stay_independent` | Meets its text |
| T-004 Huawei web app | ECS/ELB/VPC/subnet/RDS/OBS diagram; every required Huawei catalog item resolves with approved icon evidence, limited by D-018 | `huawei-web.json`: `overview` draws `vpc-web`, `elb-web`, `ecs-web`, `rds-web`, `obs-web`, `eip-egress`, `nat-egress`, `cloud-eye`, `lts` and the `cce-cluster` group, every Huawei node `custom_asset` from pack `huawei-latam-color`, no fallback; `services` adds API Gateway, FunctionGraph, IAM, VPN; `obs-web` nests under the account, not the IAM project, and notes its region. Every bundle's manifest has `rights.blockers: ["O-002"]` and the private-use limit, and `ASSET_PRIVATE_USE_ONLY` is a warning. Direct Connect is in T-006's fixture, not this one; see P3-4 | `test_t004_*` (5), `test_required_huawei_items_are_reported_by_name`, `test_the_only_blocker_is_public_distribution` | Meets its text for private personal use; the "approved" evidence is D-018, which is a risk acceptance, not cleared rights |
| T-005 On-premises | Separate physical and logical views; rack, VLAN/VRF, security zone and compute memberships retained | `onprem-physical-logical.json`: `physical` nests `physical-server-1` under `rack-b > room-a > dc-1 > site-main`; `logical` nests it by subnet and notes `location:`; the firewall keeps two networks, three subnets and three zones; `vm-1` keeps `deployment: [hypervisor-1]`; 14 device kinds present; subnet-network mismatch through VLAN/VRF refused | `test_t005_*` (5), `test_onprem_overlapping_logical_memberships_remain_valid` | Meets its text |
| T-006 Five-environment hybrid | All five environment types present; only explicitly modeled connectivity shown; trust/link labels visible | `hybrid-five.json`: `overview` has nodes and provider boxes for all five providers, five labeled `security_zone` groups; `connectivity` draws exactly four undirected links, each on-premises to one cloud, each labeled; the legend separates `peering`, `vpn`, `traffic`, `replication`; the cluster stays a compact group in the overview and its Pods are disclosed as excluded | `test_t006_*` (6) | Meets its text |

Shared checks over all six: strict validation with only `VIEW_EXCLUSIONS` and `ASSET_PRIVATE_USE_ONLY` warnings; every view draws exactly what it selects; every left-out ID is disclosed; every view's PNG is at `scale: 1.0`; every provider box holds only its provider. The 11 Kubernetes detail views now carry `type: ClusterIP` and `ports: 80:8080/TCP` on the Service, `replicas: 2` on the Deployment, `storage class:` on the PVC and `owner:` on Pods in node views, as the regenerated baselines show; the owner passed those images under D-031, and I did not open them.

## 3. Release risks

Built in this session: `uv run --frozen python -m build --no-isolation --outdir reports/dist` and `scripts/build_work_plugin.py --output reports/fable-final-work/work-plugin`, the latter both with `uv run` and with Apple's `/usr/bin/python3` 3.9.6, as the README prescribes.

| Check | Result |
|---|---|
| Wheel | `cloud_architecture_diagrams-0.5.0a1-py3-none-any.whl`, SHA-256 `4caa1f4a…6733`, equal to the wheel the S10 reproduction proof expects at `10d8398`. Holds the package, `py.typed`, `catalog_data`, `assets` (NOTICE, THIRD-PARTY-PYTHON, two OFL fonts with their notices, 15 Huawei and 8 on-premises SVG/PNG pairs) and nothing else. `METADATA` carries `Classifier: Private :: Do Not Upload`, `Requires-Python <3.14,>=3.13`, and the three runtime pins |
| sdist | `cloud_architecture_diagrams-0.5.0a1.tar.gz`: `src`, `schemas`, `scripts`, `tests` (JSON fixtures, helpers and tests; no baselines, no images), `uv.lock`, `pyproject.toml`, `README.md`, `.github` workflows, `.gitattributes`, `.gitignore`, `.python-version`. No `doc`, `plugins`, `spikes`, `assets-source`, `reports` or `.git` |
| Work plugin | Version `0.1.0-alpha.1+88ce2c0cd0dc`, the version the S09 final run and the installed cache folder name (`~/.codex/plugins/cache/mingrammer-work/cloud-architecture-work/0.1.0-alpha.1+88ce2c0cd0dc`, listed read-only) both carry. 98 files, no symbolic link, archive SHA-256 `b08f68f6…a7ec` matching its `.sha256` file, identical from both interpreters. Contents: `plugin.json`, `mcp.json`, `README.md`, `pyproject.toml`, `uv.lock`, `scripts/runtime.py`, `server/`, the skill with its guide and two examples, and the full `src` tree including the assets and notices |
| Claude Code plugin | Not a first-release deliverable (M7, deferred); its `claude-plugin` lane passed in the gate |
| Notices and licenses | `assets/NOTICE.md` names draw.io/JGraph CC BY 4.0 with the Atlassian restriction, the two Noto fonts under OFL 1.1, the icons that arrive through `diagrams` with each owner's terms, and the Huawei section that states the rights are not cleared and names D-018 and O-002. `THIRD-PARTY-PYTHON.md` lists the 21 locked packages with licenses and names Graphviz's EPL. Both ship in the wheel and the plugin |
| Private-use limit | Stated in `pyproject.toml` (classifier), `plugin.json` (`longDescription`), the README's second paragraph, `NOTICE.md`, every rendered bundle's manifest (`rights.distribution_limit`) and SVG footer (`private personal use only`), and `get_capabilities` (`release_blockers: [O-002]`). The gate's `release_blockers` names O-002 and the 17 affected Huawei types |
| Version identity | Core `0.5.0a1` in `pyproject.toml`, the wheel, `build.json` (`core_version`) and the proofs; plugin version stamped with the content digest, so any file change changes it; `lock_sha256 7df58684…cf1f` equal in the gate and the plugin build |
| Local or sensitive content | Grepped the wheel, sdist and plugin tree for `/Users/`, the owner's account names, e-mail, private keys and token shapes: no hit except the public repository URL `Rabcat-dome/mingrammer-diagram` in `plugin.json`, `reproduce_core.py` and the two workflow files, which is the repository's own name. No bundle, session record or Documents path ships |
| README install and removal | Verified against the local Codex CLI 0.166.0-alpha.6 inside the ChatGPT app: `codex plugin marketplace add`, `codex plugin add`, `codex plugin remove`, `codex plugin marketplace remove` all exist with the documented shapes. The `~/.codex/plugins/cache/mingrammer-work/cloud-architecture-work/*/scripts/runtime.py` path matches the installed layout. `runtime.py remove` deletes only `env-*`, `setup.lock` and `setup-failure.json` under `~/.local/share/cloud-architecture-diagrams/work-plugin` and keeps bundles, as the README says. The build command works with Apple's `python3` 3.9.6. The README's runtime and bundle paths match `runtime.py:152-154`. `test_readme_states_the_modes_rights_and_the_whole_lifecycle` pins the command strings |
| Supported host modes | README table, `HOST_MODES` in `runtime.py:43-55` and `get_capabilities` agree: selected is the ChatGPT desktop app in Work mode on macOS Apple silicon; web, mobile and cloud threads are not supported; Intel Macs, Windows/Linux and Codex are not verified. This matches the evidence: two Apple silicon Macs, full-access chats, GPT-6.1 Sol only, no stricter-approval run. The README's "may ask you to approve" stands on the second Mac's single allow prompt that the session record does not hold |
| Core reproduction proof | `S10-core-reproduction-proof.json` at `10d8398`: `source_digest 9e82dcb8…1bb58` equals `reproduce_core.source_digest()` computed at `e167deb` in this session, so the proof describes this head's `src`, references, lock, `pyproject.toml` and baseline digests; the 12 files that changed after `10d8398` are all under `doc/`. The second Mac's proof at `fd3cc80` describes the earlier source and is recorded as such |

Residual release risks, all recorded and none new: Huawei rights (O-002, private use only under D-018); the Huawei preview bytes reach the chat host (D-026); single model and single person's accounts on both Macs; the final plugin version ran on one Mac (D-032); no stricter-approval chat has run.

## 4. The P0 report

Sampled 36 of 71 records, weighted to those D-027 to D-032 moved, comparing each with the requirement text and opening its named tests. The `release-audit` lane, which passed, already proves each named test exists and each link resolves.

| Record | State | Verdict |
|---|---|---|
| FR-004 | met_with_owner | Fair. Core tests reject duplicates, dangling refs and cycles; the note says plainly that cross-edit stability rests on the skill and the Work runs |
| FR-005 | met_with_owner | Fair. The note says what it accepts: one model, one Mac, full access |
| FR-010, FR-011, FR-012 | met_with_owner | Fair. `test_every_rule_has_a_negative_case_and_every_emitted_code_is_declared` ties every rule to a negative case and every emitted code to a rule; `test_every_catalog_type_appears_in_a_passing_fixture` covers positives. The notes name D-030's per-rule choice; FR-012's names D-016 |
| FR-013 | met_with_owner | Fair, and honest: the note says the icons are not approved and rest on D-018/D-019 |
| FR-014 | met_with_owner | Fair. The new `test_the_onprem_pack_terms_reach_the_bundle_and_the_notice` closes the source-conditions gap S10 named |
| FR-018 | met | Slightly generous: one of its 14 checks is the name-only test in P3-2, and P3-1 shows a case where a configuration reference leaves the drawing. The other checks and the baselines carry the claim for the shipped fixtures. Keeping `met` is defensible; the record should not cite `test_every_kind_of_typed_reference_has_a_note` as a renderer check |
| FR-021 | met_with_owner | Fair; the note defers appropriateness to D-023 and T-016 |
| FR-022 | met_with_owner | Fair; the note states the accepted hole (S08 P3-8) and why |
| FR-025, NFR-006 | met | Fair. `test_every_view_draws_exactly_what_it_selects` and `test_a_left_out_id_is_disclosed_for_every_view` are the real checks |
| FR-029 | met_with_owner | Fair; the note says `management` has no endpoint rule and gives the reason. P3-1 is a consequence of that choice |
| FR-048 | met_with_owner | Fair and candid: no automated fidelity check, by-eye comparison in M4 only |
| FR-050 | met | Fair. The two new version-lock tests fail for the right reason, and the requirement was reworded by D-030 to what is built |
| FR-060, FR-062, T-011, T-013, T-017 | met_with_owner | Fair. Each note names D-027 and states one Mac, full access, one model. T-017's named tests cover the M1/M2/M4 parts; the Work part is the owner's report |
| FR-064, FR-066, T-010, NFR-001 | met_with_owner | Fair, and consistent with S09-Work-validation.md and M6-second-machine.md: each note carries D-029 and then D-032's caveat that the final version passed on the first Mac only and the second Mac passed the version before it. The records do not claim the final version on two machines |
| FR-065 | met_with_owner | Fair. `test_core_stays_free_of_the_host_adapter` is an AST and text check on `src`; the note says test reuse has no check of its own |
| NFR-009 | met_with_owner | Fair. The new limits test pins the numbers; the note says memory and temporary limits are sampled |
| NFR-014 | met_with_owner | Fair; D-023 for the Thai sample |
| T-001 to T-006 | met_with_owner | Fair; each names D-023 and says acceptance in Work is M5/M6's. T-002's note states the VPN reading (P3-4) |
| T-012 | met_with_owner | Fair; the P1 clause is deferred by D-030 and the P0 rejection tests are real (`test_view_size_limits_reject_with_a_split_suggestion`, `test_an_in_bound_view_over_the_pixel_limit_asks_for_a_split`) |
| T-015 | partly | Correct. Its `open` text says no release SHA exists; this review is M6-03, and M6-04 follows the owner's disposition. `test_the_wheel_installs_alone_and_renders_from_outside_the_repository` really installs the built wheel with hash-locked packages and renders the Huawei `services` view from elsewhere |
| T-016 | met_with_owner | Fair; D-023 and D-031, with the note that the lane detects change, not fidelity |

No sampled state is too generous beyond the FR-018 nuance above, and every `met_with_owner` note names its decision and says what it accepts. The D-032 and T-010 records agree with `S09-Work-validation.md#final-version` (final version, first Mac, five passes, four bundles re-rendered identically from `main`) and with `M6-second-machine.md` (earlier version, second Mac, 26 views reproduced). The report page's intro sentence was corrected in `e167deb` to say M6-03 and M6-04 have not run; after this review the owner can regenerate it.

## 5. Unresolved findings

Every finding still open in `doc/project-management/evidence`, with its source, and a block or no-block call for a private personal release.

| Source | Finding | Severity | Block? |
|---|---|---|---|
| S11-gpt-reviews G3, D-026 | The Work plugin returns a Huawei view's preview and file bytes to the chat host | P2 (Medium), accepted by the owner in D-026 and stated in the README | No: a justified Medium with owner disposition, which M6's exit allows |
| S07-fable-review P3-1 | Sandbox reads are allowed by default outside `$HOME` | P3 | No: hardening; the renderer runs local-only on the owner's Macs |
| S07 P3-2 | Unicode bidi and format controls pass validation and can reorder label text | P3 | No: a model the owner's own chat writes |
| S07 P3-3 | `test_every_render_code_is_exercised_by_a_test` matches strings only | P3 | No: test strength |
| S07 P3-5 | Unconfirmed millisecond window between publish and stdout where a signal could escape as a traceback | P3 | No: never reproduced; bundle on disk is complete |
| S08-fable-review P3-2 | A left-right edge from above stops at a node's invisible top | P3 | No: stated as a deviation; owner accepted the images |
| S08 P3-8 remainder | A subnet with no path to any network accepts any `network_ref` | P3, accepted by D-030 as FR-022's unspecified fact | No |
| S08 P3-12 | A nesting loop across two dimensions is broken in ID order | P3, stated in the contract | No |
| S08 P3-13 | Reaching the nesting pass bound would be silent | P3, never constructed | No |
| S09-fable-review P3-9 | A cancel landing after the core finished leaves a bundle the client is not told about | P3 | No: `list_bundles` shows it |
| S09 P3-12 | `scripts/runtime.py` labels any `OSError` as `OUTPUT_ROOT_UNAVAILABLE` | P3 | No: terminal only, exit code right |
| S09 P3-13 | `ARTIFACT_UNSAFE` wording on a permission-denied root | P3 | No |
| S10-fable-review P3-A | The reproduction proof's digest leaves out the graph baselines, `reproduce_core.py` and the engine | P3 | No: `visual-regression` fails on those changes; the engine is recorded in the proof |
| S10 P3-C | A record's `note` is hidden when it also has `open` text; no record does this | P3 | No |
| S10 P3-D | `THIRD-PARTY-PYTHON.md` says "for this platform" while the walker ignores markers; identical today | P3 | No |
| S11-fable-lock-review P3-1, also D-028 | `remove` deletes `setup.lock` without taking the lock, so a `remove` during a running setup lets a second setup start | P3 | No: needs a terminal `remove` during a chat's first setup on the same Mac |
| S11-fable-lock-review P3-2, also D-028 | One half of `test_setup_waits_out_a_readiness_check_but_not_a_setup` goes through a private helper | P3 | No: test strength |
| S11-astra-short N1, N2 | Fixed at `ae8520f`+, and the record says no independent review covers that last change | Limit, not a finding | No: the gate's `release-audit` lane with its 67 tests passed here |
| S06-provider-catalogs N2, N3, N4 | Fargate profile in another VPC accepted; EKS cluster may declare subnets in two VPCs; a Pod's NodePool edge is not reconciled with `node_ref` | P3, deferred with reasons in the contract | No |
| M7-fable-review, three P3 | Claude plugin wrapper: no regression test for the relative-`HOME` check; a damaged private environment never heals; the wrapper fails through an outside symlink | P3 | No: M7 is not a first-release deliverable |
| This review P3-1 to P3-4 | Above | P3 | No |

In M6's terms: no Critical or High finding remains open anywhere in the records or from this review; the one Medium (G3) has the owner's disposition in D-026; everything else open is P3 and, by the model strategy the records cite, waits for the owner.

## What I ran and what I did not

Ran:

- `uv run --frozen python scripts/quality_gate.py` once, in the background: 17 lanes passed, 1,585 tests, 0 skipped, at `e167deb` with a clean tree, Python 3.13.7, uv 0.13.0, Graphviz 16.1.0, Darwin arm64 (`reports/quality-gate.json`, `reports/fable-final-work/quality-gate.out`).
- The wheel and sdist build, the Work plugin build twice (uv's Python 3.13.7 and Apple's 3.9.6), the archive checksum, and the unpacking and grepping of all three.
- `probe_step1.py`, `probe_step1b.py`, `probe_step2.py`: 30-odd renders of mutated reference models through the real renderer and engine, under a throwaway `HOME`, with every output under `reports/fable-final-work/`.
- `reproduce_core.source_digest()` at this head, and SHA-256 of the built wheel, against the S10 proof.
- `codex plugin --help` and `codex plugin marketplace --help` from the ChatGPT app's bundled CLI, and a read-only listing of the plugin cache folder names.

Did not run or read:

- Actual ChatGPT Work, a second machine, the fresh-clone `reproduce_core.py`, or CI. The Work results are the owner's reports as recorded.
- Any PNG or SVG image, by instruction; graphs and manifests only.
- Mutation of tracked files for sabotage checks; P3-2 is by reading.
- The S11 Sol and Astra reports in full; I read their findings tables and the Claude session's disposition of them.
- The remaining 35 P0 records beyond the sample, the full `test_work_plugin.py` (2,200+ lines) beyond the tests the sampled records name, and the Claude Code plugin's runtime.
- A `remove` or `prune` against the installed runtime, or anything under `~/Documents/CloudArchitectureDiagrams` or `~/.codex`, beyond listing folder names.

## Disposition

**Approved for tagging** at `e167deb79702127f516ef8d95630a2a16dc604af`, as the private personal release M6 describes: Huawei icons for the owner's private use only under D-018 and O-002, two Apple silicon Macs, Work mode in the ChatGPT desktop app. The four P3 findings above can wait for the owner, and P3-1 is the one I would fix first if the owner wants a change before tagging, because it is small and it touches what FR-018 promises. This approves nothing beyond what it states, and it does not replace the owner's own inspection or their run in Work.
