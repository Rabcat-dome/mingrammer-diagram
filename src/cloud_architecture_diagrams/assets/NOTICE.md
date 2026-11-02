# Third-party visual assets

This inventory satisfies NFR-004 and FR-052 for this package. The machine-readable record, with source versions, terms and SHA-256 digests, is `catalog_data/assets.json`.

## Bundled here

The eight SVG and PNG pairs under `assets/onprem` are derived from Network 2018 shapes from [draw.io](https://github.com/jgraph/drawio), copyright JGraph Ltd, licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Source: release v29.3.2, `src/main/webapp/stencils/networks.xml`.

**Changes:** the stencil geometry was converted to SVG, the palette's default colors were applied, the result was rasterized to PNG, and the hypervisor and identity-service assets each combine two shapes. draw.io has not reviewed or endorsed these derivatives.

**Restriction from the source's stencil license:** these icon sets and any derivatives may not be displayed within, distributed for use with, or incorporated into products distributed through the Atlassian marketplace or plugin ecosystem without explicit written permission from draw.io. This package is not distributed there.

## Not bundled: delivered by the `diagrams` dependency

| Icons | Rights | Conditions |
|---|---|---|
| AWS | AWS allows them for creating architecture diagrams | Diagrams only |
| Azure | Microsoft permits them in architectural diagrams, training materials and documentation | No cropping, flipping, rotating or distortion |
| Google Cloud | Google's official library offers them for diagrams and technical documentation; no separate license text is stated | Diagrams and technical documentation only |
| Kubernetes resources | The Kubernetes Authors, Apache-2.0 (chosen from Apache-2.0 or CC-BY-4.0) | The Kubernetes logo stays subject to The Linux Foundation's trademark guidelines |
| Generic and on-premises | `mingrammer/diagrams`, MIT, copyright 2020 MinJae Kwon | Unbranded symbols only |

The product names and icons above belong to their owners, and no endorsement is implied.

## Not available: Huawei Cloud icons

No Huawei Cloud icon is included. Huawei Cloud's site terms require prior written consent to reproduce or distribute site content and express written permission to use its logos, and no license or consent has been found. Open decision O-002 tracks this as a release blocker. Catalog entries keep their native names and semantic rules, with no generic substitute.
