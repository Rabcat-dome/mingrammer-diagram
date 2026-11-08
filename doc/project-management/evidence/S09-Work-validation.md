# S09 ChatGPT Work Acceptance Check

Target: the separate ChatGPT Work page or mode, not Codex (D-014). Automated checks and rehearsals stay in the [S09 evidence](S09-work-plugin.md), and only what the owner reports below counts as a Work result.

**Status: all five checks pass in Work on the final version, `0.1.0-alpha.1+88ce2c0cd0dc`, on the first Mac (D-032), after passing on `0.1.0-alpha.1+d27ef23f6f94` on both Macs (D-027, D-029). M5 closed on 2026-11-05 under D-028.** **After the release, the five prompts and a sixth pass on `0.1.0-alpha.1+80cadf16a121` on the first Mac (D-042), as [After the release](#after-the-release) records.** **On `0.1.0-alpha.1+5fc47e5a0839`, prompt 1 and check 5 pass (D-043), and the chat shows the plugin's images unchanged, as [The image rule in Work](#the-image-rule-in-work) records.** **On `0.1.0-alpha.1+594b3683feb0`, four prompts written for D-044 pass (D-045), and the first model of each drawing names `metadata.environment`, as [The missing field in Work](#the-missing-field-in-work) records.** **On `0.1.0-alpha.1+f6b9f6134e60`, three prompts written for D-046 pass (D-047), and the chat names every item a view leaves out, by name and ID, as [Naming what a view leaves out in Work](#naming-what-a-view-leaves-out-in-work) records.**

## What the owner runs

Install, from a checkout of `main`, with the commands in the [plugin README](../../../plugins/cloud-architecture-work/README.md#install). Then restart the ChatGPT app, switch to Work mode, open a new chat and select **Cloud Architecture Diagrams**. The S04 plugin stays enabled and unchanged.

The final version is `0.1.0-alpha.1+88ce2c0cd0dc`, which adds [D-030's detail lines](M6-p0-gaps.md#fr-018) to the [S11 fixes](S11-gpt-reviews.md#fixes) and the fix for the [second run's fault](#second-run). A change to the plugin's content changes its version, so a fix after this needs its own run. Each prompt runs in the same chat unless it says otherwise.

| # | Prompt | What it checks |
|---|---|---|
| 1 | `Use Cloud Architecture Diagrams. Check that its runtime is ready, set it up if it is not, and tell me the plugin version, the runtime state, whether rendering is available and any blockers.` | Install, discovery, approval prompt, setup, version |
| 2 | `Draw an AWS three-tier web application: an Application Load Balancer, two EC2 app servers and an RDS database in one VPC. Show me the picture and give me all six files.` | Rendering, preview, retrieval |
| 3 | `In that diagram, add an S3 bucket that both app servers read from, and draw it again. Keep everything else as it is. Tell me which IDs you kept and added.` | Edit flow, stable IDs, updated source |
| 4 | `Validate this model and tell me what is wrong, without fixing it: {"schema_version":"1.0.0","metadata":{"id":"x","title":"X","environment":"prod","assumptions":[]},"resources":[{"id":"app","name":"App","provider":"aws","service_type":"aws.compute.ec2","taxonomy":"compute.vm"}],"relationships":[{"id":"r1","source_ref":"app","target_ref":"ghost","kind":"traffic"}],"views":[{"id":"v","title":"V","entity_refs":["app"]}]}` | Invalid input: expects `REFERENCE_MISSING` and no image |
| 5 | Do not paste this row. Paste a Thai sentence asking for a GKE architecture with a Deployment, Service, Ingress and PVC, with both an overview view and a detail view, and with Thai names on the labels. The session that started this check gives the exact sentence, because repository documents stay English. Pasting this row made a chat draft a sentence and call no tool | Kubernetes overview and detail, Thai labels, same IDs in both views |

## S17's bands in Work

Run on 2026-11-08 and 2026-11-09 (Asia/Bangkok) on `0.1.0-alpha.1+fee9566f6d58`, with core `0.7.0a1`, built from `60e72f8`, on the first Mac, in one new Work chat outside this repository, after the owner restarted the ChatGPT app. The runtime was `ready`, so `setup_runtime` did not run. The session record, started at 23:54:24, has originator `codex_work_desktop` and GPT-6.1 Sol / High, with approval policy `never` and `danger-full-access`, on `codex-cli 0.167.0-alpha.3.2`. A Claude Opus 5.5 session wrote prompts 2 to 4 for [S17](S17-compass-bands.md), and drew a model of its own for each through the installed plugin before handing them over. Prompt 4 was meant for a new chat but ran in the same one, after the chat had written bands for prompts 2 and 3, so this run does not show whether the Thai request alone leads a new chat to bands.

| # | Prompt | What it checks |
|---|---|---|
| 1 | Prompt 1 of [the edit rule's run](#the-drawio-edit-rule-in-work), naming the plugin | Version and runtime |
| 2 | `Use Cloud Architecture Diagrams to draw a north-south and east-west network picture of an Azure web application in two regions, Southeast Asia as primary and East Asia as standby. From north to south: internet users; Azure Front Door; an Application Gateway in each region; two virtual machines in each region; an Azure Database for PostgreSQL flexible server in each region; a VPN Gateway in the primary region; and the head office firewall on-premises at the bottom. Draw the global peering between the two VNets and the database replication from primary to standby east-west. Show me the picture and give me all the files.` | Bands in the order asked, and both east-west lines level |
| 3 | `In that diagram, add an Azure Firewall in each region between the Application Gateway and the virtual machines, on a row of its own, and draw it again. Keep everything else as it is. Tell me which IDs you kept, added and removed.` | A new band in its place, and the IDs kept, added and removed |
| 4 | A Thai sentence, translated here: "Use Cloud Architecture Diagrams to draw a north south east west network architecture of a web system in Huawei Cloud's Bangkok region: users come in through an ELB to two ECS (AZ1 and AZ2), which use a primary GaussDB in AZ1 that replicates to a standby in AZ2, and a VPN links to the firewall at head office. Thai names on every label. Show the picture and give me all the files." | Bands from the style's name alone, Thai labels, and the private-use limit |

The owner passed the run (D-057) and asked for the guide rule the last finding below calls for. The rest was checked from the session record and the files.

| Check | Result |
|---|---|
| 1. Install and runtime | The chat used this plugin and reported this version, core `0.7.0a1`, the runtime `ready` on Python 3.13.7, rendering available and no blockers. It also named the Huawei Cloud private-use limit |
| 2. Azure | Strict with no diagnostics. The final view is `TB` with eight bands from north to south: the internet users, Front Door, both Application Gateways, the four VMs, both PostgreSQL servers, both VNets, the VPN Gateway and the head office firewall. The VNets' band is the chat's own, giving the peering a row. `east_west_refs` holds the peering and the replication. In the picture each band is one row, the users sit above the Azure box and the firewall below it, and both east-west lines run level. The chat drew it three times, moving the VNets' band each time, and turned the legend off |
| 3. Firewall row | Strict with no diagnostics. A `firewall` band holds both Azure Firewalls between the gateways and the VMs, each in its own `AzureFirewallSubnet`. The chat listed 11 IDs added, the four gateway-to-VM lines removed and every other ID kept, which matches the two models exactly. It added an assumption that traffic is routed through the firewalls |
| 4. Huawei Cloud with Thai labels | Strict with the one `ASSET_PRIVATE_USE_ONLY` warning. The chat chose six bands from the users to the head office firewall, with the replication east-west. It chose `physical` grouping, with the region and both zones, and modelled no VPC, subnet or scope, as the prompt named none. In the picture the users are at the top, the firewall at the bottom, and the replication runs level and meets both icons. The labels are Thai, and the chat said which text stays in English and relayed the private-use limit. Its summary called the servers' lines to the database east-west, though only the replication is drawn level |

Other things seen in the session record and the files:

- For checks 2 to 4 the chat showed the plugin's own image and linked copies of all seven files of each final bundle, in its workspace's `outputs` folder. All 21 copies match their bundles byte for byte.
- The chat rendered seven times. Six gave bundles, and one was refused with `SCHEMA_FIELD_INVALID`, because an assumption the chat lengthened ran to 331 characters, over the bound of 256. It split the text and drew again. It ran 15 web searches on Microsoft and Huawei Cloud pages, searched the installed plugin's renderer source for how east-west lines and anchors are drawn, and read no memory file.
- **The peering line in the first Azure render was not level.** The chat's VNets' band sat between the VMs and the databases, and the four lines between those rows carry text of up to four lines, from their label, protocol and purpose. dot puts a line's text on the middle row it crosses, which was the VNets' row, so the texts sat between the peering line's ends and the line rose 31 pt in the SVG. Laid out again from `main`, the line is level without those texts, with the VNets' band in either of the chat's later places, or with the VNets in no band. The guide said to band whatever sits between a level line's ends, but not that a crossing line's text counts. D-057 adds that rule, and a render test holds the bend on the compass fixture.

Rendering the three final models again from `main` at `946ec7a` gives the same `diagram.svg`, `diagram.png`, `diagram.drawio`, `model.json`, `view.json` and `diagnostics.json`, and the manifests differ only in `bundle_id`. Bundles under `~/Documents/CloudArchitectureDiagrams/work/`: Azure `azure-web-two-region--network-view--58a6c7b2114c6227`, after `--19f3f5569eb14bb4` and `--57a3909653d3f19d`, the firewall row `--60b1bbe6be3e5ed2`, and Huawei Cloud `huawei-bangkok-web-network--network-view--07b85f7dc7a045ba`, after `--1947f79e64b9901b`. This run covers one Mac and one model, under full access, with a runtime that was already set up.

## S16's types in Work

Run on 2026-11-08 (Asia/Bangkok) on `0.1.0-alpha.1+8d2e5b054083`, with core `0.6.0a1` and catalog `2026.11.3`, built from `bfbce78`, on the first Mac, in one new Work chat outside this repository, after the owner restarted the ChatGPT app. The runtime was `ready`, so `setup_runtime` did not run. The session record, started at 18:42:33, has originator `codex_work_desktop` and GPT-6.1 Sol / High, with approval policy `never` and `danger-full-access`, on `codex-cli 0.167.0-alpha.3.2`. A Claude Opus 5.5 session wrote prompts 2 to 5 for [S16](S16-catalog-coverage.md), each naming services that only S16's types draw.

| # | Prompt | What it checks |
|---|---|---|
| 1 | Prompt 1 of [the edit rule's run](#the-drawio-edit-rule-in-work), naming the plugin | Version and runtime |
| 2 | `Use Cloud Architecture Diagrams to draw an Azure web application: Azure Front Door in front of an App Service web app, with a function app for background jobs, both using VNet integration. The web app reads Cosmos DB and Azure Managed Redis. The function app reads Service Bus and writes to a PostgreSQL flexible server. Secrets are in Key Vault, reached through a private endpoint. Show me the picture and give me all the files.` | Strict, with delegated subnets and a private endpoint attached to Key Vault |
| 3 | `Use Cloud Architecture Diagrams to draw an AWS network: two VPCs joined by a Transit Gateway. In the first VPC, an Application Load Balancer with an ACM certificate sends traffic to EC2 instances, which reach SQS through an interface VPC endpoint and S3 through a gateway VPC endpoint. CloudFront sits in front of the load balancer and is protected by Shield Advanced. GuardDuty and CloudTrail are enabled. Show me the picture and give me all the files.` | Strict, with an attachment per VPC, endpoints in their network forms, and Shield and the certificate attached |
| 4 | `Use Cloud Architecture Diagrams to draw a GCP application: a Cloud DNS public zone and a global external Application Load Balancer with Cloud Armor and Cloud CDN, in front of Compute Engine instances. The instances publish to a Pub/Sub topic and read a secret from Secret Manager encrypted with a Cloud KMS key. Show me the picture and give me all the files.` | Strict, with Armor and CDN attached to the global load balancer |
| 5 | A Thai sentence, translated here: "Use Cloud Architecture Diagrams to draw a system on Huawei Cloud: an ELB in front of two ECS, DCS for Redis as the cache, GaussDB as the database, DMS for Kafka for events, EVS disks attached to the ECS, and backups with CBR. Thai names on every label. Show the picture and give me all the files." | Strict with Thai labels, EVS and CBR attached, and the private-use limit |

The owner passed the run (D-054). The rest was checked from the session record and the files.

| Check | Result |
|---|---|
| 1. Install and runtime | Passed. The chat used this plugin and reported this version, with the runtime `ready`, rendering available and no blockers |
| 2. Azure | Passed. The model, with `environment` `"design"`, drew strict with no diagnostics and used nine new types: Front Door, App Service, a function app, Cosmos DB, Azure Managed Redis, Service Bus, a PostgreSQL flexible server, Key Vault and a private endpoint. Each app has its own delegated integration subnet, PostgreSQL its own subnet, and the private endpoint its subnet, attached to Key Vault |
| 3. AWS | Passed. The model drew strict, with only `VIEW_EXCLUSIONS` for the two zones, and used eight new types: Transit Gateway, two VPC attachments, interface and gateway VPC endpoints, a Shield protection, an ACM certificate, GuardDuty and CloudTrail. Each attachment lists one subnet per zone of its VPC, the gateway endpoint lists no subnet, Shield attaches to CloudFront and the certificate to the ALB. The chat named both zones the overview leaves out, by name and ID |
| 4. GCP | Passed. The model drew strict with no diagnostics and used six new types: a Cloud DNS public zone, a Cloud Armor policy, Cloud CDN, a Pub/Sub topic, a Secret Manager secret and a global Cloud KMS key. Armor and CDN attach to the global external Application Load Balancer |
| 5. Huawei Cloud with Thai labels | Passed. The model, with `environment` in Thai, drew strict with the one `ASSET_PRIVATE_USE_ONLY` warning and used five new types: DCS for Redis, GaussDB, DMS for Kafka, two EVS disks and a CBR vault. The chat drew each ECS to its disk and each disk to the vault, the opposite way from the records' targets, and S16's reading of an attachment either way accepted both. It answered in Thai, said which text stays in English, and relayed the private-use limit |

Other things seen in the session record and the files:

- For checks 2 to 5 the chat showed the plugin's own images and linked all seven files of each final bundle. All 28 copies match their bundles byte for byte.
- No model held an unknown type, and none was a lenient draft.
- The chat rendered eight times, and searched the web 11 times for Azure, AWS, GCP and Huawei Cloud pages. It read no memory file, and no `busy` answer or failed validation appeared.

Rendering the four final models again from `main` at `bfbce78` gives the same `diagram.svg`, `diagram.png`, `diagram.drawio`, `model.json`, `view.json` and `diagnostics.json`, and the manifests differ only in `bundle_id`. Bundles under `~/Documents/CloudArchitectureDiagrams/work/`: Azure `azure-web-application--overview--b3f307477c742d60`, after `--797f1ac874bbaed5`, AWS `aws-transit-gateway-network--overview--170fd1f8a7b06077`, GCP `gcp-web-application--overview--cf92fbe465d1733f`, after `--96b8fcf2a2fd5be1`, and Huawei Cloud `huawei-cloud-application--overview--02a16376e8b0c874`, after `--70d749fcd9a82603` and `--8a1513341855a777`. This run covers one Mac and one model, under full access, with a runtime that was already set up.

## The draw.io edit rule in Work

Run on 2026-11-08 (Asia/Bangkok) on `0.1.0-alpha.1+4ce48c4beb7c`, with core `0.6.0a1`, built from `ef792fc`, on the first Mac, in one new Work chat outside this repository, after the owner restarted the ChatGPT app. The runtime was `ready`, so `setup_runtime` did not run. The session record, started at 16:23:30, has originator `codex_work_desktop` and GPT-6.1 Sol / High, with approval policy `never` and `danger-full-access`, on `codex-cli 0.167.0-alpha.3.2`. It runs prompt 3 of [the run before](#the-drawio-copy-in-work) again on [D-051's rule](S15-polyline-and-drawio.md#the-drawio-edit-rule), after prompt 2 to give it a drawing. Prompt 1 now names the plugin, because the run before reached the S04 plugin.

| # | Prompt | What it checks |
|---|---|---|
| 1 | `Use the Cloud Architecture Diagrams Work plugin, cloud-architecture-work. Check that its runtime is ready, set it up if it is not, and tell me the plugin version, the runtime state, whether rendering is available and any blockers.` | Version and runtime |
| 2 | Prompt 2 of the run before | All seven files, and a drawing for prompt 3 |
| 3 | Prompt 3 of the run before | The change goes through the model and a new render, and the new bundle's `diagram.drawio` is handed over unchanged |

The owner passed the run (D-052). The rest was checked from the session record and the files.

| Check | Result |
|---|---|
| 1. Install and runtime | Passed. The chat used this plugin and did not touch the S04 plugin. It reported this version and core `0.6.0a1`, with the runtime `ready`, rendering available and no blockers, and said the saved render probe had passed on `0.1.0-alpha.1+a0465bcceca9`, which the runtime's `probed_with` shows |
| 2. GCP, all files | Passed. One model, with `environment` `"design"`, passed strict with no diagnostics, and the chat rendered it three times to settle the title, direction and names. It copied the final bundle's seven files with a checksum check and linked all seven, `diagram.drawio` as "Editable draw.io diagram". All seven copies match the bundle byte for byte |
| 3. Editing the draw.io file | Passed, with two gaps. The chat read the bundle's `model.json`, added Cloud Monitoring and two `observability` relationships with every earlier ID kept, validated it and rendered a new bundle. It checked that the model changed only by those additions, then copied the new bundle's `diagram.drawio` unchanged as `diagram-with-cloud-monitoring.drawio`, and said that the export recalculated the layout. It wrote no draw.io file of its own. It did not show the new picture or link the new bundle's other six files, and did not say that changes made by hand in draw.io are not carried over, which D-051's paragraph asks for |

Other things seen in the session record and the files:

- The draw.io desktop app exported the new bundle's `diagram.drawio` with the same groups, icons, lines with their bends, and labels as its PNG, in draw.io's own font.
- The chat made no draw.io export and no other file of its own. Prompt 2 searched the web once for Google Cloud documents. The chat read no memory file.
- No `busy` answer and no `RUNTIME_INSTALLING` appeared.

Rendering both final models again from `main` at `ef792fc` gives the same `diagram.svg`, `diagram.png`, `diagram.drawio`, `model.json`, `view.json` and `diagnostics.json`, and the manifests differ only in `bundle_id`. Bundles under `~/Documents/CloudArchitectureDiagrams/work/`: GCP `gcp-web-application--overview--619ad9411520f66b`, after `--c35fc31989af8fa9` and `--0be7b0e606e6d381`, and the GCP view with Cloud Monitoring `--1289eb39d24640cf`. This run covers one Mac and one model, under full access, with a runtime that was already set up.

## The draw.io copy in Work

Run on 2026-11-08 (Asia/Bangkok) on `0.1.0-alpha.1+a0465bcceca9`, with core `0.6.0a1`, built from `94b426c`, on the first Mac, in one new Work chat outside this repository, after the owner restarted the ChatGPT app. The runtime was `ready`, so `setup_runtime` did not run. The session record, started at 15:34:54, has originator `codex_work_desktop` and GPT-6.1 Sol / High, with approval policy `never` and `danger-full-access`, on `codex-cli 0.167.0-alpha.3.2`. A Claude Opus 5.5 session wrote prompts 2 to 4 for [D-048 and D-049](S15-polyline-and-drawio.md). Prompt 2 names neither draw.io nor the number of files.

| # | Prompt | What it checks |
|---|---|---|
| 1 | The table's prompt 1 | Version and runtime |
| 2 | `Use Cloud Architecture Diagrams to draw a GCP web application: a global external Application Load Balancer in front of two Compute Engine instances in one subnet of a VPC. Both instances read and write a Cloud SQL database and read images from a Cloud Storage bucket. Show me the picture and give me all the files.` | All seven files, `diagram.drawio` among them, said to open in draw.io without being asked |
| 3 | `Open that draw.io file, add Cloud Monitoring that watches both instances, and give me the updated draw.io file.` | The change goes through the model and a new render, and the new bundle's `diagram.drawio` is handed over unchanged |
| 4 | A Thai sentence, translated here: "Use Cloud Architecture Diagrams to draw a web architecture on Huawei Cloud: an ELB in front of two ECS in the same subnet of a VPC, and both read and write an RDS database. Thai names on every label. Show the picture, and give me a file I can edit further in draw.io." | Thai labels and Huawei icons in the draw.io copy, handed over unchanged |

The rest was checked from the session record and the files.

| Check | Result |
|---|---|
| 1. Install and runtime | Not shown by this prompt. The chat chose the S04 plugin, `0.1.0-alpha.3`: it read that plugin's skill, called its runtime check, rendered its three-node sample and reported that version. It did not run S04's setup, and S04's state file still has its time from 10:05. In prompt 2, `get_capabilities` reported this version and core `0.6.0a1`, with the runtime `ready`, rendering available and no blockers |
| 2. GCP, all files | Passed. One model, with `environment` `"conceptual"`, passed strict with no diagnostics, and the chat rendered it twice, the second time to retitle the view, turn off the legend and rename four resources. It linked all seven files of the final bundle under "All seven files", `diagram.drawio` as "Editable diagram: Open in draw.io", without being asked. All seven copies match the bundle byte for byte |
| 3. Editing the draw.io file | Failed. The chat added Cloud Monitoring and two `observability` relationships to the model, which passed strict, and rendered a new bundle. It then wrote a draw.io file of its own: the earlier `diagram.drawio` with the new resource and lines copied in from the new bundle, the resource placed by hand, both lines without their bends, in another colour, dash pattern and width, with set end points. It handed over that file, `gcp-web-application-monitoring.drawio`, saying it had preserved the existing layout, and neither showed the new picture nor linked the new bundle's files. The file matches no PNG or SVG in any bundle, and six of its style keys are ones the plugin's check refuses |
| 4. Huawei with Thai labels | Passed. One model, with `environment` in Thai, passed strict with the one `ASSET_PRIVATE_USE_ONLY` warning, and the chat rendered it twice, the second time to rename the subnet. It linked the bundle's `diagram.drawio` first, after opening it in draw.io to check, then the other six files. It said in Thai which text stays in English, and that the Huawei icons are for private use only. All seven copies match the bundle byte for byte |

Other things seen in the session record and the files:

- The draw.io desktop app exported each bundle's `diagram.drawio` with the same groups, icons, lines with their bends, and labels as its PNG, in draw.io's own font: the GCP view of prompt 2, the GCP view with Cloud Monitoring of prompt 3, and the Huawei view, whose Thai labels and two notice lines are plain text.
- Prompts 2 to 4 searched the web for Google Cloud and Huawei Cloud documents. The chat read no memory file.
- No `busy` answer and no `RUNTIME_INSTALLING` appeared.

Rendering the three final models again from `main` at `94b426c` gives the same `diagram.svg`, `diagram.png`, `diagram.drawio`, `model.json`, `view.json` and `diagnostics.json`, and the manifests differ only in `bundle_id`. Bundles under `~/Documents/CloudArchitectureDiagrams/work/`: GCP `gcp-web-application--overview--3e40a3a50e7b3090`, after `--bcf477505f8217ca`, the GCP view with Cloud Monitoring `--8b38b7b00330c32c`, and Huawei `huawei-web-application--overview--4f6453d93ea06e84`, after `--630ad24a9d8db327`. The bundle `demo--overview--73956c34167d561c` is from the install check.

The owner chose to fix the skill rather than pass the run (D-051). See [the draw.io edit rule](S15-polyline-and-drawio.md#the-drawio-edit-rule). Prompt 3 ran again on the fixed plugin, in [the next run](#the-drawio-edit-rule-in-work), which the owner passed with this one (D-052).

## Naming what a view leaves out in Work

Run on 2026-11-08 (Asia/Bangkok) on `0.1.0-alpha.1+f6b9f6134e60`, with core `0.5.0a3`, built from `9b77c56`, on the first Mac, in one new Work chat outside this repository, after the owner restarted the ChatGPT app. The runtime was `ready`, so `setup_runtime` did not run. The session record, started at 10:03:57, has originator `codex_work_desktop` and GPT-6.1 Sol / High, with approval policy `never` and `danger-full-access`, on `codex-cli 0.167.0-alpha.3.2`. A Claude Opus 5.5 session wrote prompts 2 to 4 for [D-046](S09-exclusion-disclosure.md), and none of them asks the chat what a view leaves out. Prompt 2's model was first validated, and its overview rendered, through both installed plugins, and the installed Work server's `disclose` for it is the expected answer.

| # | Prompt | What it checks |
|---|---|---|
| 1 | The table's prompt 1 | Version and runtime |
| 2 | `Validate this model and draw its overview view. Do not change the model.`, followed by a GCP model, `shop-gcp`. Its overview selects the load balancer, the web server, the database and the line between the first two, and its detail view selects everything | Six items named: `bucket`, `project`, `vpc`, `subnet`, and the relationships `images` and `orders`. The overview draws a `subnet: App subnet` note, which must not stand in for naming `subnet` |
| 3 | `Use Cloud Architecture Diagrams to draw an AWS web application: a CloudFront distribution in front of an Application Load Balancer, two EC2 instances in private subnets in two Availability Zones, an ElastiCache cluster for sessions, and an RDS database. Make an overview view with only the request path and a detail view with everything. Show me both pictures and give me all six files of each.` | Every item a view leaves out is named, the zones included |
| 4 | A Thai sentence, translated here: "Use Cloud Architecture Diagrams to draw an application architecture on AKS with a Deployment, Service, Ingress, ConfigMap and Secret. I want one overview picture and one detail picture, with Thai names on every label. Show both pictures and give the six files of each." | The same, with Thai names |

The owner passed the run (D-047). The rest was checked from the session record and the files.

| Check | Result |
|---|---|
| 1. Install and runtime | Passed. The chat reports this version and core `0.5.0a3`, with the runtime `ready`, rendering available and no blockers, and it rendered a sample through the plugin. The list below records what it also did with the S04 plugin |
| 2. Fixed GCP model | Passed. The model passed strict with only `VIEW_EXCLUSIONS`, and the bundle's `model.json` equals the prompt's model. The chat named all six items that `disclose` lists, each by its name and ID, the two relationships by their ends. It gave its reason after them: the Orders database appears without a line because the overview leaves out `orders`. It did not use the subnet note in place of `subnet` |
| 3. AWS overview and detail | Passed. One model, with `environment` `"conceptual"`, passed strict. The chat named all 14 items the overview leaves out, by name and ID, in its own order: the Region, the VPC, `az-a` and `az-b`, four subnets, the cache, the database, and four relationships with their labels. It said the detail view leaves nothing out, which matches the render, whose answer has no `disclose` |
| 4. AKS with Thai labels | Passed. One model, with `environment` the Thai for "conceptual", passed strict. The chat answered in Thai and named all four items the overview leaves out by their Thai names and their IDs: the ConfigMap, the Secret and the Deployment's two lines to them. It gave the two relationships by their ends without their labels, which the skill does not ask for |

This is the first run in Work in which the chat named every item a view leaves out. Under D-043 and D-045 it gave a reason in place of some items, or left some out.

Other things seen in the session record and the files:

- In prompt 1 the chat also checked the S04 plugin, `0.1.0-alpha.3`, which stays enabled. Its startup check failed with "system binary changed", so the chat ran that plugin's own `scripts/setup.py`. At 10:05 this rewrote the S04 state file, `~/.local/share/cloud-architecture-diagrams/0.1.0-alpha.3.json`, with new fingerprints of its executables, and copied its two fonts and `fonts.conf` again. It checked the S04 Python packages and changed none, and no file of the installed S04 plugin changed. The chat then rendered S04's three-node sample, bundle `601f48826cec892e2928e9353495fad1`. The Homebrew Graphviz and fontconfig folders date from 2026-11-01, so which executable changed is not known. This changes the state of the S04 runtime, which [What the owner runs](#what-the-owner-runs) expects to stay unchanged, although prompt 1 asks the chat to set the runtime up if it is not ready.
- For checks 2 to 4 the chat showed the plugin's own images. It copied the six files of each of the five bundles into its folder and checked them, and all 30 copies match the bundles byte for byte. Each drawing's two views share one `model.json`.
- Prompts 3 and 4 searched the web for AWS, Azure and Kubernetes documents. The chat read no memory file.
- No `busy` answer and no `RUNTIME_INSTALLING` appeared.

Rendering the five views again from `main` at `9b77c56` gives the same `diagram.svg`, `diagram.png`, `model.json`, `view.json` and `diagnostics.json`, and the manifests differ only in `bundle_id`. Bundles under `~/Documents/CloudArchitectureDiagrams/work/`: the sample `demo--overview--092c171cd6e24eae`, GCP `shop-gcp--overview--6280b8ca51ef3e2d`, AWS `aws-web-application--overview--250c346b1256cf23` and `aws-web-application--detail--38373a0cc3110a23`, and AKS `aks-app-thai--overview--a4d0f8e14895930d` and `aks-app-thai--detail--6f305bacc14a0468`. This run covers one Mac and one model, under full access, with a runtime that was already set up. The table's prompts 2, 3 and 5 and [the sixth prompt](#after-the-release) did not run on this version.

## The missing field in Work

Run on 2026-11-08 (Asia/Bangkok) on `0.1.0-alpha.1+594b3683feb0`, with core `0.5.0a3`, built from `54a7b11`, on the first Mac, in one new Work chat outside this repository, after the owner restarted the ChatGPT app. The runtime was `ready`, and the chat's render probe passed, so `setup_runtime` did not run. The session record, started at 00:24:50, has originator `codex_work_desktop` and GPT-6.1 Sol / High, with approval policy `never` and `danger-full-access`. A Claude Opus 5.5 session wrote prompts 2 to 4 for [D-044](S09-missing-field.md). Prompts 2 and 3 ask for architectures no earlier Work chat drew, so the app's memory could not hand the chat a model that already held `environment`.

| # | Prompt | What it checks |
|---|---|---|
| 1 | The table's prompt 1 | Version and runtime |
| 2 | `Draw an AWS architecture: an Application Load Balancer in front of an ECS service running on Fargate in two private subnets of one VPC. The service reads and writes an RDS database and pulls its images from ECR. Show me the picture and give me all six files.` | The first model names `metadata.environment` |
| 3 | A Thai sentence, translated here: "Use Cloud Architecture Diagrams to draw a web architecture on Azure: an Application Gateway in front of two VMs in the same VNet, and both VMs read and write an Azure SQL Database. Put Thai names on every label. Show the picture and give me all six files." | `environment` written in the labels' language, and the image rule |
| 4 | `Validate this model and tell me what is wrong, without fixing it: {"schema_version":"1.0.0","metadata":{"id":"x","title":"X","assumptions":[]},"resources":[{"id":"app","name":"App","provider":"aws","service_type":"aws.compute.ec2","taxonomy":"compute.vm"}],"relationships":[],"views":[{"id":"v","title":"V","entity_refs":["app"]}]}` | A missing field: expects `SCHEMA_FIELD_MISSING` at `/metadata/environment` and no image |

The owner passed the run (D-045). The owner did not report separately on how the images appeared or whether the files opened. The rest was checked from the session record and the files.

| Check | Result |
|---|---|
| 1. Install and runtime | Passed. The chat reports this version and core `0.5.0a3`, with the runtime `ready`, rendering available and no blockers. It ran the runtime's render probe by importing the plugin's server code with `python3`, not through a tool |
| 2. AWS on ECS and Fargate | Passed. The first model held `"environment": "conceptual"` and passed strict at once, with only a `VIEW_EXCLUSIONS` warning for the two zones. This is the first of seven Work sessions whose first model did not fail on `metadata.environment`. The chat rendered three times: to shorten four names, retitle the view and add the service's `attachment` lines to both subnets and its `membership` line to the cluster, then to turn the view top to bottom. The final view's title draws as "Application architecture (conceptual)", and it uses the ALB, ECS cluster, Fargate for ECS, RDS and ECR types |
| 3. Azure with Thai labels | Passed. The first model held an `environment` written in Thai, translated here as "conceptual", and passed strict at once with no diagnostics. The title draws as the Thai for "Web system overview" with that word in brackets. The chat told the user, in Thai, that the titles, resource names, network names and arrow labels are Thai, and that type labels the plugin adds, such as `Subnet` and `Azure SQL Database`, stay in English |
| 4. Missing field | Passed. `SCHEMA_FIELD_MISSING` at `/metadata/environment`, with the message and remedy D-044 sets, and no bundle. The chat said validation stopped at the schema and left the model unchanged |

Other things seen in the session record and the files:

- For checks 2 and 3 the chat showed the plugin's own images. It copied each final bundle's six files into its folder with `shutil.copyfile` and checked each copy's SHA-256 against the renderer's, and in check 3 it also checked the SVG's text for every Thai label. All 12 copies match the bundles byte for byte.
- In check 2 the chat said that the overview shows the zones as subnet labels, but did not name `az-a` and `az-b` as left out of the view, although the skill asks it to disclose every view's exclusions. This is close to what [the image rule in Work](#the-image-rule-in-work) records.
- In prompt 1 the chat read the runtime skill and scripts of the old S04 plugin, and the app's memory summary of an earlier runtime chat. It read no memory in prompts 2 to 4, and both models were written fresh.
- Prompts 2 and 3 searched the web for AWS and Azure documents.
- No `busy` answer and no `RUNTIME_INSTALLING` appeared.

Rendering both final models again from `main` at `8d39d0f` gives the same `diagram.svg`, `diagram.png`, `model.json`, `view.json` and `diagnostics.json`, and the manifests differ only in `bundle_id`. Bundles under `~/Documents/CloudArchitectureDiagrams/work/`: AWS `aws-alb-ecs-fargate-rds-ecr--overview--acc5053d40bf13e8`, after `--85d5706b6d7014c5` and `--d4397177ba684ff6`, and Azure `azure-web-gateway-vms-sql-th--overview--aec032ebb1f7a96f`. This run covers one Mac and one model, under full access, with a runtime that was already set up. The table's prompts 2, 3 and 5 and [the sixth prompt](#after-the-release) did not run on this version, and prompt 4 ran in the changed form above.

## The image rule in Work

Run on 2026-11-07 (Asia/Bangkok) on `0.1.0-alpha.1+5fc47e5a0839`, built from `9388fee`, on the first Mac, in one new Work chat outside this repository, after the ChatGPT app was restarted. The runtime was `ready`, with a passing render probe under this version, so `setup_runtime` did not run. The session record has originator `codex_work_desktop` and GPT-6.1 Sol / High, with approval policy `never` and `danger-full-access`. Prompt 1 is the table's. The second prompt is check 5's Thai sentence, the same as in [After the release](#after-the-release). Prompts 2, 3, 4 and 6 did not run on this version.

The owner passed the run (D-043). The owner did not report separately on how the images appeared or whether the files opened. The rest was checked from the session record and the files.

| Check | Result |
|---|---|
| 1. Install and runtime | Passed. The chat reports this version and core `0.5.0a2`, with the runtime `ready`, rendering available and no blockers. It rendered the plugin's sample and copied its six files unchanged |
| 5. GKE with Thai labels | Passed. The chat showed the plugin's own images. It copied each bundle's six files into its folder with `cp`, and checked each copy's SHA-256 against the plugin's. All 12 copies match the bundles byte for byte, and no command edited, translated, redrew or converted an image. It told the user, in Thai, that the names, titles and arrow labels are Thai, and that type names, text on icons and values the plugin adds stay in English. Both views share one `model.json`, SHA-256 `04a3cad5892ada5ec4d0a001fd72cf3afbf209f81ed1b3e7940c21c9905b4368`, and every name, title and relationship label in it is Thai |

Other things seen in the session record and the images:

- English appears where the skill says: `Google Cloud`, each type name, `node: unspecified` in both views, and `type: ClusterIP` and `replicas: 1` only in the detail view.
- The first model failed with `SCHEMA_FIELD_INVALID` on `metadata.environment`, as check 2 did in earlier runs. The chat read the schema and corrected it. D-044 [addresses the cause](S09-missing-field.md).
- The chat said that the overview leaves the ReplicaSet and PV to the detail view. It did not list the three relationships the overview also leaves out, or the Deployment to Pod line the detail view leaves out, although the skill asks it to disclose every view's exclusions.
- The app's memory listed an earlier GKE chat and its model `gke-web-with-pvc`, but the chat wrote a new model, `gke-app-th`, and did not read the earlier one.
- As before, the chat read the runtime skill of the old S04 plugin in prompt 1, and searched the web for GKE and Kubernetes documents.
- No `busy` answer and no `RUNTIME_INSTALLING` appeared.

Rendering both views again from `main` at `f22b75d` gives the same `diagram.svg`, `diagram.png` and `view.json`. Bundles under `~/Documents/CloudArchitectureDiagrams/work/`: GKE `gke-app-th--overview--cbde6c612099cbcc` and `gke-app-th--detail--e1461b068491d8ce`, and the sample `demo--overview--4ee9a80323d3e908`. This run covers one Mac and one model, under full access, with a runtime that was already set up, and two of the six prompts.

## After the release

Run on 2026-11-07 (Asia/Bangkok) on `0.1.0-alpha.1+80cadf16a121`, built from `5598159`, on the first Mac, in one new Work chat outside this repository. The runtime stayed as its setup that day left it, `ready` with a passing render probe, so `setup_runtime` did not run. The session record has originator `codex_work_desktop` and GPT-6.1 Sol / High, with approval policy `never` and `danger-full-access`. Prompts 1 to 4 are the table's. Prompt 5 was a Thai sentence, translated here: "Use Cloud Architecture Diagrams to draw an application architecture on GKE with a Deployment, Service, Ingress and PVC. I want both an overview and a detail view, with Thai names on every label." A sixth prompt, for the AWS types of S12 and S13, asked for a CloudFront distribution protected by a CloudFront web ACL, in front of an API Gateway HTTP API, with a Lambda function behind it that reads and writes a DynamoDB table, and a Cognito user pool for sign-in.

The owner passed all six and asked for the skill change below (D-042). The owner did not report separately on how the images appeared or whether the files opened. The rest was checked from the session record and the files.

| Check | Result |
|---|---|
| 1. Install and runtime | Passed. The chat reports this version and core `0.5.0a2`, with the runtime `ready`, rendering available and no blockers |
| 2. AWS drawing | Passed. The first model failed with `SCHEMA_FIELD_INVALID` on its `environment`, and the chat read the schema and corrected it, as in the earlier run. Strict, no warnings, and all six files |
| 3. Edit | Passed. All 11 IDs stayed unchanged: the model's own, the view, the VPC, four resources and four relationships. `s3`, `app-1-to-s3` and `app-2-to-s3` were added. The chat rendered twice, the second time only to name each read line's server in its label |
| 4. Invalid model | Passed. `REFERENCE_MISSING` at `/relationships/0/target_ref`, and no bundle |
| 5. GKE with Thai labels | Passed on the plugin's bundles, which the chat did not show, as the next paragraph says. Both views share one `model.json`, SHA-256 `e3477a3831a8d43921e396b33aaa2de8daf11a1b701b0616fb53be694ba75eca`, and the Thai names and labels draw. The detail view shows the D-030 lines and follows S14's rule: the Ingress keeps its `service:` note, because its line to the Service is `dependency`, not `traffic`, and the PVC's storage class note hides, because a `storage` line from the PVC draws it |
| 6. AWS serverless | Passed. Strict, no warnings, with `aws.network.cloudfront`, `aws.security.waf_cloudfront`, `aws.integration.api_gateway_v2`, `aws.compute.lambda`, `aws.database.dynamodb` and `aws.identity.cognito_user_pool`. This is the first live session to use S13's types |

For check 5, the chat did not show the plugin's images. It judged that the English text the renderer adds broke the request for Thai on every label, so it changed `diagram.svg` itself. It translated the provider headings, deleted each node's type name, and rewrote the property lines in Thai, losing `TCP` and `app=web`. Then it drew the PNG again with `rsvg-convert`, outside the sandbox and the font check. It linked the plugin's six files beside them as a ZIP. The skills of both plugins now forbid this, and say which text stays in English (D-042).

Other things seen in the session record:

- The chat started check 5's model from the GKE chat of 2026-11-05, through the app's memory and that chat's bundle, so that model was not written fresh.
- The chat read the plugin's `src` and server code in prompts 1, 3 and 5, and the runtime skill of the old S04 plugin, which stays installed.
- In prompt 3, the lines to S3 start short of the EC2 icons, which is S08's open P3-2.
- Prompt 6 also searched the web for AWS documents.
- No `busy` answer and no `RUNTIME_INSTALLING` appeared.

Rendering the five final bundles again from `main` gives the same `diagram.svg`, `diagram.png` and `view.json`. Bundles under `~/Documents/CloudArchitectureDiagrams/work/`:

- AWS `aws-three-tier-web-app--overview--16f6e9c6c9645a75`, and after the edit `aws-three-tier-web-app--overview--b0d81fdd84d860f6`
- GKE `gke-web-with-pvc--overview--148c236ad466e6fe` and `gke-web-with-pvc--detail--77312d4c8ee9383f`
- AWS serverless `aws-serverless-http-api--overview--61cf1e2cf18e3e56`

Claude Fable 5.1 [approved the skill change and this record](S09-fable-image-rule-review.md) with four P3 findings, and they are [fixed](S09-fable-image-rule-review.md#fixes). Its [review of the fixes](S09-fable-image-rule-review.md#review-of-the-fixes) left three P3 findings, which are [fixed too](S09-fable-image-rule-review.md#fixes-after-the-second-review), and [a third review](S09-fable-image-rule-review.md#review-of-the-second-fixes) approved those fixes with two P3 findings in the records, which are [fixed too](S09-fable-image-rule-review.md#fixes-after-the-third-review). The change and its fixes make the Work plugin `0.1.0-alpha.1+5fc47e5a0839`, which is installed on the first Mac from `9388fee` and passes [the run of the image rule](#the-image-rule-in-work) (D-043). This run covers one Mac and one model, under full access, with a runtime that was already set up.

## Final version

Run on 2026-11-05 on `0.1.0-alpha.1+88ce2c0cd0dc`, on the first Mac, in one new Work chat outside this repository, after removing the runtime. The session record has originator `codex_work_desktop` and GPT-6.1 Sol / High, with approval policy `never` and `danger-full-access`. The owner passed all five. The rest was checked from the session record and the files.

| Check | Result |
|---|---|
| 1. Install and runtime | Passed. The chat reports this version, and setup reaches `ready` from `RUNTIME_NOT_READY` |
| 2. AWS drawing | Passed. Strict, no warnings, and all six files |
| 3. Edit | Passed. All 11 IDs stayed: the model's own, the view, the VPC, four resources and four relationships. `s3-bucket`, `app-1-s3` and `app-2-s3` were added, and no existing resource or relationship changed |
| 4. Invalid model | Passed. `REFERENCE_MISSING`, and no bundle |
| 5. GKE with Thai labels | Passed, at the second attempt. The first paste was this page's own table row, so the chat drafted a sentence and called no tool, and its row now says not to. The drafted sentence then ran. Both views share one model, and the detail view shows D-030's new `type: ClusterIP` line, with no such line in the overview |

Rendering all four bundles again from `main` gives the same `diagram.svg`, `diagram.png` and `view.json`. No `busy` answer and no `RUNTIME_INSTALLING` appeared. Bundles under `~/Documents/CloudArchitectureDiagrams/work/`:

- AWS `aws-three-tier-web--overview--aa1d14ba097e636c`, and after the edit `aws-three-tier-web--overview--dc0cb58ed135873a`
- GKE `gke-thai-application--overview--4ddc97f3f718c736` and `gke-thai-application--detail--6cd7d16ed1f478fa`

The model in this run declared a Service type and no replicas or ports, so only `type:` was seen in Work. Tests and the owner's [reference images](M6-p0-gaps.md#fr-018) cover the other lines. The second Mac did not run this version (D-032).

## Result

This is the run on `0.1.0-alpha.1+d27ef23f6f94`, which closed M5.

Run on 2026-11-05 (Asia/Bangkok) in one new Work chat, with GPT-6.1 Sol / High, in a folder outside this repository, after removing the runtime. The session record has originator `codex_work_desktop`. "Owner" marks what only the owner could see, and the rest was checked from the session record and the files.

| Check | Result |
|---|---|
| Plugin visible and selectable in Work | Passed. The owner's prompts selected it by its `plugin://` link |
| Version the chat reports | `0.1.0-alpha.1+d27ef23f6f94`, as expected |
| An approval prompt for `setup_runtime`, and what it looked like | None. Owner: the chat had full access, so the app did not ask. The session record has approval policy `never` and `danger-full-access`. How the app asks under a stricter setting is unverified |
| Runtime reaches `ready` | Passed, in about 20 seconds from a removed runtime with a warm uv cache: `RUNTIME_NOT_READY`, `setup_runtime`, then `ready`. The marker names this version |
| PNG visible in the chat, and how it appeared | Passed. Owner: it appears as a normal image and can be downloaded |
| All six files open from Work | Passed. Owner: they open. Each bundle holds all six. The chat copied them to its own `outputs` folder by shell, and read `model.json` through `read_artifact` for the edit |
| Edit keeps IDs and returns the updated source | Passed. All 11 IDs stayed: the model's own, the view, the VPC, four resources and four relationships. `s3`, `app-1-to-s3` and `app-2-to-s3` were added, and nothing else in the model changed. The new bundle holds the updated source |
| Invalid model gives `REFERENCE_MISSING` and no image | Passed, at `/relationships/0/target_ref`, and no bundle was made |
| Kubernetes overview and detail both draw, with readable Thai | Passed. Both views share one model, so their IDs agree. Owner: passed |
| Anything unexpected | The chat's first AWS model failed with two `SCHEMA_FIELD_INVALID`, and it read the schema and corrected the model, which is the flow the skill describes. No `busy` answer, and no `RUNTIME_INSTALLING` |

Rendering all four bundles again from `main` gives the same `diagram.svg`, `diagram.png` and `view.json`. Bundles under `~/Documents/CloudArchitectureDiagrams/work/`:

- AWS `aws-three-tier-web-app--overview--a6fa5cb47c9027c8`, and after the edit `aws-three-tier-web-app--overview--3e6416cdcb809f60`
- GKE `gke-web-app-th--overview--35a48b517c883c69` and `gke-web-app-th--detail--11eaebee4341d42f`

Four more Work chats ran at the same time, each with one of prompts 2 to 5 and the same version. They drew their own bundles, and none of the five chats saw `RUNTIME_INSTALLING`, which is what the second run's fault would have shown.

This result has limits:

- One Mac and one model. A second machine, a Python download and the system's Documents prompt stay for M6.
- The main chat read the plugin's skill and no `src`. It also read the runtime skill of the old S04 plugin, which stays installed, so this is not a run with this plugin alone.
- The chats had full access, so nothing here shows how the app asks under a stricter setting.

## Earlier runs

These ran on earlier versions, and are the history of how this result came about.

### First run

Run on 2026-11-04 (Asia/Bangkok) in one chat, with GPT-6.1 Sol / High. The owner reports that the run was in Work, and the host's session record agrees: its originator is `codex_work_desktop`, where a Codex session on this Mac the same day has `Codex Desktop`.

| Check | Result |
|---|---|
| Plugin visible and selectable in Work | Passed. The owner's prompt selected it by its `plugin://` link |
| Version the chat reports | `0.1.0-alpha.1+f242304382f3`, as expected |
| An approval prompt for `setup_runtime`, and what it looked like | None in the session record, where the chat's approval policy is `never`. Whether the app showed one is not yet reported |
| Runtime reaches `ready` | Passed, in under a minute: `RUNTIME_NOT_READY`, then `RUNTIME_INSTALLING`, then `ready` |
| PNG visible in the chat, and how it appeared | Both render results held an image, the answer embedded both, and the owner accepted that answer. How they appeared is not yet reported |
| All six files open from Work | Partly. All six files of both bundles came back through `read_artifact`, after a [retry](#busy-answers). Whether the answer's file links open is not yet reported |
| Edit keeps IDs and returns the updated source | Not run |
| Invalid model gives `REFERENCE_MISSING` and no image | Not run |
| Kubernetes overview and detail both draw, with readable Thai | [Passed](#check-5-in-work) |
| Anything unexpected | [Four `busy` answers](#busy-answers), and the chat calling its own run Codex |

### Check 5 in Work

The local `cloud-architecture-work` plugin validated the GKE model in strict mode and rendered both views with readable Thai labels. The detail view was rendered from the overview bundle's model. Ingress (`app-ingress`), Service (`app-service`), Deployment (`app-deployment`) and PVC (`app-pvc`) kept the same IDs in both views. The two `model.json` files have the same SHA-256 (`11a52f4a43debd030ec31d8abf11cc8fed3de4c4e6e3a1991b08e87301cdc7a7`). The owner then told the chat, translated from Thai: "record that it passed."

Bundles under `~/Documents/CloudArchitectureDiagrams/work/`:

- Overview `gke-web-storage--overview--4269037e6861b375`
- Detail `gke-web-storage--detail--20c28cf1dcd9775d`

The chat first recorded this as a Codex run with the Work result pending. The owner corrected that, and this page now follows the owner and the session record.

This run has limits as acceptance evidence:

- The chat was not new. An earlier turn had read this repository's records and run its tests, and the repository was its working folder.
- It read `src` while writing the model, so it does not show that the plugin's skill alone is enough.
- The prompt was not the sentence this check planned. It also asked outright to keep the IDs.

#### What the Claude session checked on disk

The owner's Claude Code session checked the files and the host's session record the same day. It read the chat's prompts, its messages to the owner, and the tool names and statuses, so this is not a second opinion on what the app showed.

- The installed plugin's files equal the build, and its version is the expected one.
- Both bundles exist with the digest above, both are `complete`, and `diagnostics.json` says `strict`. Its only diagnostics are `VIEW_EXCLUSIONS` warnings, for each view's disclosed exclusions.
- Rendering each view again from the repository at `aefcdbc` gives the same `diagram.svg`, `diagram.png` and `view.json`. The four IDs are in both graphs, and the ReplicaSet is only in the detail view.
- These are the only bundles in the folder, so no AWS bundle from checks 2 and 3 exists on this Mac. The session record shows no such prompt either.

### Busy answers

The chat read 12 files at once, all six of both bundles. Eight came back and four answered `busy` with `TOO_MANY_CALLS`, and it read those four again one at a time, which worked. `MAX_CALLS` is 8 in `protocol.py`, and no render was running. Sending 12 reads at once to the installed server again gave 4, 4 and 3 refusals in three tries, while 6 and 8 reads gave none.

At that version the skill's `busy` row said "Another render is running", which was the wrong cause although its remedy worked, and no test covered `TOO_MANY_CALLS`. [S11](S11-gpt-reviews.md#fixes) fixed both.

### Second run

Run on 2026-11-05 on `0.1.0-alpha.1+2c3c9ea4f01c`, in a new Work chat. The session record has `codex_work_desktop` and GPT-6.1 Sol / High. The chat ran prompt 5's sentence as written, with the plugin selected, and no other prompt. The owner reported that the test was done, and has not yet said what the app showed or whether this run passes.

The Claude session checked these from the files and the session record:

- Both views validate in strict mode and draw. Both `model.json` files have the digest beginning `7be07b30`, so the IDs are the same in both views. Rendering each view again from `main` at `d5007d4` gives the same `diagram.svg`, `diagram.png` and `view.json`.
- The runtime was already `ready`, so no setup ran, and this run says nothing about an approval prompt.
- The chat read the plugin's skill, model guide and Kubernetes example. It did not read `src`, so this run supports the skill being enough, which the first could not. Its working folder was still this repository, and it ran `git status` and looked for `AGENTS.md` there.
- It read no file through `read_artifact`, and its answer embedded both images and linked all six files.

**A fault this run found.** One of five `search_catalog` calls sent at once answered `runtime_unavailable` with `RUNTIME_INSTALLING`, though the runtime was ready and no setup was running. The chat retried, and that worked. `_setup_locked_elsewhere` tests for a running setup by taking the setup lock exclusively without waiting, so two calls testing at once collide, and one reads the other as a setup. On the installed server with its ready runtime, 21 of 100 calls sent in fives gave this answer. The Claude session ranked it P2, because ordinary use reaches it and it states something false, though no data was at risk and waiting cleared it. No test covered readiness under parallel calls, and no reviewer found it.

The readiness test now takes the lock shared, which only a setup's exclusive lock can refuse, and a setup waits up to a second for a test to finish before it reports that another setup holds the lock. Three tests cover this, one of them sending the same parallel calls to the real server, and all 6 sabotage changes fail one of them. Actual CI [run 41958019512](https://github.com/Rabcat-dome/mingrammer-diagram/actions/runs/41958019512) passed 17 lanes and 1,569 tests at `b0a8b4d`. Under D-021, Claude Fable 5.1 / Medium [approved it](S11-fable-lock-review.md) in a fresh agent, and found no way to run two setups at once or to report a ready runtime as installing, with threads or with several processes. Two P3 findings stay open: `remove` deletes the lock file without taking the lock, which predates this fix, and one half of a new test goes through a private helper.
