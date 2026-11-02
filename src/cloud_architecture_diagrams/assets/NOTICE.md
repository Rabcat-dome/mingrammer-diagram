# Third-party visual assets

This inventory covers NFR-004 and FR-052 for this package. The machine-readable record, with source versions, terms and SHA-256 digests, is `catalog_data/assets.json`.

## Bundled: on-premises symbols

The eight SVG and PNG pairs under `assets/onprem` are derived from Network 2018 shapes from [draw.io](https://github.com/jgraph/drawio), copyright JGraph Ltd, licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Source: release v29.3.2, `src/main/webapp/stencils/networks.xml`.

**Changes:** the stencil geometry was converted to SVG, the palette's default colors were applied, the result was rasterized to PNG, and the hypervisor and identity-service assets each combine two shapes. draw.io has not reviewed or endorsed these derivatives.

**Restriction from the source's stencil license:** these icon sets and any derivatives may not be displayed within, distributed for use with, or incorporated into products distributed through the Atlassian marketplace or plugin ecosystem without explicit written permission from draw.io. This package is not distributed there.

## Not bundled: delivered by the `diagrams` dependency

| Icons | Rights | Conditions |
|---|---|---|
| AWS | AWS allows them for creating architecture diagrams | Diagrams only |
| Azure | Microsoft permits them in architectural diagrams, training materials and documentation | No cropping, flipping, rotating or distortion |
| Google Cloud | Google's official library offers them for diagrams and technical documentation; no separate license text is stated. The owner accepted them under D-016 | Diagrams and technical documentation only |
| Kubernetes resources | The Kubernetes Authors, Apache-2.0 (chosen from Apache-2.0 or CC-BY-4.0) | The Kubernetes logo stays subject to The Linux Foundation's trademark guidelines |
| Generic and on-premises | `mingrammer/diagrams`, MIT, copyright 2020 MinJae Kwon | Unbranded symbols only |

The product names and icons above belong to their owners, and no endorsement is implied.

## Bundled for private personal use only: Huawei Cloud icons

**These rights are not cleared.** The 15 SVG and PNG pairs under `assets/huawei` are included only because the owner of this private plugin accepted the rights risk for their own private personal use under decision D-018. No rights holder has granted permission, and no redistribution permission has been established. Do not publish this package, this plugin or these files, and do not make its repository public. O-002 keeps public distribution blocked.

**Source:** the color group of [huaweicloud-latam/drawio-libraries at commit 52c33aa](https://github.com/huaweicloud-latam/drawio-libraries/tree/52c33aa12fb816a5de403da85067e1c0f039b5be/color). That account is named HUAWEI CLOUD LATAM and links to Huawei Cloud, but it is not a verified organization, its repository has no license, and its corporate authorization is not established. Huawei Cloud names and marks belong to Huawei.

**Changes:** each SVG holds the bytes decoded from its library entry, and each PNG is rasterized from that SVG.

## Not available

Huawei's official icon library and other Huawei icon packs are not included. Huawei Cloud's site terms require prior written consent to reproduce or distribute site content and express written permission to use its logos.
