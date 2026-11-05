# M6-04 — The Personal Release

Date: 2026-11-05 (Asia/Bangkok) | Tag: `v0.1.0-alpha.1` | Decision: D-033

**Result: M6 is closed, and `v0.1.0-alpha.1` is the first release, for the owner's private personal use.** It is a tag on this private repository. There is no GitHub Release and no uploaded package, because the packages hold Huawei icons whose rights are not cleared (D-018, O-002). Build them from the tag.

## What the tag identifies

| Item | Value |
|---|---|
| Work plugin | `0.1.0-alpha.1+88ce2c0cd0dc`, 98 files |
| Plugin ZIP | `cloud-architecture-work-0.1.0-alpha.1+88ce2c0cd0dc.zip`, SHA-256 `b08f68f68b82cbd5063feb5ccd4c7ca768734515615067e558845673f079a7ec` |
| Core | `0.5.0a1`, catalog `2026.11.0` |
| Wheel | `cloud_architecture_diagrams-0.5.0a1-py3-none-any.whl`, SHA-256 `4caa1f4a96833d3a2402ce9252794c6256c75deb4e7a673b954e11785226d733` |
| Source archive | `cloud_architecture_diagrams-0.5.0a1.tar.gz`, SHA-256 `00c8d0bc02317105bb0686004128f7ce55d22887297fd15152b4b20f99b7e5ff` |
| Dependency lock | `uv.lock`, SHA-256 `7df586841f346fac7fd6a46c81db5f632db581538199861d825f5cb47565cf2f` |
| Tested with | Python 3.13.7, Graphviz 16.1.0, and uv 0.13.0 and 0.13.7, on Apple silicon Macs |

Building twice gives the same wheel and source archive, and [the core proof](S10-core-reproduction-proof.json) matches this wheel from a new clone with its own Python and packages.

## Install, upgrade and roll back

From a checkout at the tag, the [plugin README](../../../plugins/cloud-architecture-work/README.md#install) gives the install, upgrade and removal commands, and they were run on two Macs. Each Mac needs `uv`, Graphviz and `python3`. To move the plugin to another Mac, copy the ZIP privately, check its SHA-256, and install from its unpacked folder, as [M6-01](M6-second-machine.md) did.

To roll back, check out the earlier commit, build the plugin over the same folder and add it again, as for an upgrade, then restart the app and open a new chat. A version with the same `uv.lock` reuses its runtime. Bundles are never removed by any of this, and each records the versions that made it.

## What the evidence covers

| Exit item | Evidence |
|---|---|
| All P0 pass | [The report](S10-p0-traceability.md): 32 met and 39 met with the owner's acceptance, of 71. Each acceptance names its decision and what it accepts |
| No unresolved Critical or High, and Medium findings have the owner's disposition | [The final review](M6-fable-final-review.md#5-unresolved-findings): none Critical or High, and the one Medium, G3, has D-026 |
| Work acceptance on two machines | [The final version](S09-Work-validation.md#final-version) on the first Mac, and [the version before it](M6-second-machine.md) on the second, which the owner accepts under D-032 |
| Clean-runtime reproduction | [The first Mac's proof](S10-core-reproduction-proof.json) describes this source, and [the second Mac's](M6-second-machine-proof.json) the source before D-030 |
| Provider image acceptance | D-023 for 15 views, and D-031 for the 11 Kubernetes detail views |

Fable/High approved tagging at `e167deb`. The commits after it change only records, and the sentence the P0 report's page opens with.

## Limits

- **Private personal use only.** Do not publish this package, share it in a workspace or make this repository public. Huawei rights are not cleared, and O-002 blocks public distribution.
- **Tested narrowly.** Two Apple silicon Macs on one person's accounts, one model, GPT-6.1 Sol, and full-access chats. How the app asks under a stricter setting is unverified, and Intel Macs, Windows, Linux, the web and mobile are not supported or not verified, as the README states.
- **Previews reach the chat host**, including Huawei icons (D-026).
- **Open findings.** The [final review](M6-fable-final-review.md#5-unresolved-findings) lists every open P3. Its P3-1 is the first to fix: a selected edge of another kind between two entities hides a typed reference's note. Fixing it changes the plugin's version, so it waits for the next release.
- **The reviews share limits.** The final review shares a vendor with the implementer, and no GPT model has reviewed D-030's code.
