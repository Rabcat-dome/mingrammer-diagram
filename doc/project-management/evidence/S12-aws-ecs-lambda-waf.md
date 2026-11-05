# S12 — AWS ECS, Fargate for ECS, Lambda and WAF

Date: 2026-11-05 | Branch: `codex/aws-ecs-fargate-lambda-waf`, from `a4bf065` | Decision: D-034

**Result: strict validation and rendering now accept five new AWS types, each with one taxonomy ID, a placement rule from AWS's own pages and AWS's own icon. The branch is not merged, the tag `v0.1.0-alpha.1` does not move, and no live session has used it yet.**

## Why

[M7's live sessions](M7-claude-plugin.md#what-real-use-found) ended two of two AWS requests as lenient drafts, because the catalog had no ECS, Lambda or WAF, and Fargate only as the EKS profile. These sat outside the P0 list, so this is selected P1 coverage, and the inventory in requirements section 6 does not change.

The gap was confirmed before editing, with `cloud-diagrams catalog --provider aws --query <term>` at `a4bf065`: `ecs`, `lambda` and `waf` returned no records, and `fargate` returned only `aws.containers.eks_fargate_profile`.

## The types

| Type | Native ID | Taxonomy | Icon class in `diagrams` 0.25.1 | Location | Network |
|---|---|---|---|---|---|
| `aws.containers.ecs_cluster` | `AWS::ECS::Cluster` | `compute.containers` | `aws.compute.ElasticContainerService` | Regional | None |
| `aws.containers.ecs_service` | `AWS::ECS::Service` | `compute.containers` | `aws.compute.ElasticContainerServiceService` | Regional | One VPC, at most 16 subnets |
| `aws.containers.ecs_fargate` | `AWS::ECS::Service` | `compute.containers` | `aws.compute.Fargate` | Regional | One VPC, at most 16 subnets |
| `aws.compute.lambda` | `AWS::Lambda::Function` | `compute.serverless` | `aws.compute.Lambda` | Regional | Optional: one VPC, at most 16 subnets |
| `aws.security.waf` | `AWS::WAFv2::WebACL` | `security.control` | `aws.security.WAF` | Regional | None |

The brief named ECS as "cluster or service". Both are here, because they follow opposite network rules and a request usually names both. **No other type was added.** Fargate shares `AWS::ECS::Service` with the general service, as the NAT gateway variants share one native ID, because the difference changes a rule: Fargate has no EC2 host.

The catalog gained one capability, `container_workload`, because no existing one described a service, and one placement field, `attachment_targets`. Both are additive, so the schema stays at 1.0.0. Five rule codes are new: `PLACEMENT_HOST_REGION_MISMATCH`, `PLACEMENT_ATTACHMENT_TARGET_INVALID`, `AWS_ECS_CLUSTER_MULTIPLE`, `AWS_WAF_RESOURCE_REGION_MISMATCH` and `AWS_WAF_ACL_MULTIPLE`.

![The new types in one picture](S12-aws-ecs-lambda-waf.png)

## What each rule rests on

Each page was fetched on 2026-11-05 and is recorded in `S06-source-checks.json`, where these 15 pages carry their own `checked` date. The patterns there match the page text, as in S06. The quotes below are AWS's.

| Rule | AWS says | Source |
|---|---|---|
| An ECS cluster is one logical, regional group | "logical grouping of tasks or services"; "Clusters are AWS Region specific" | [Clusters](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/clusters.html) |
| A cluster takes no network | Its seven properties name no VPC or subnet | [`AWS::ECS::Cluster`](https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-ecs-cluster.html) |
| A workload's subnets share one VPC, at most 16 | "All specified subnets must be from the same VPC"; "limit of 16 subnets" | [AwsVpcConfiguration](https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_AwsVpcConfiguration.html) |
| A service names one cluster | "the cluster that you run your service on" | [`AWS::ECS::Service`](https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-ecs-service.html) |
| Fargate has no EC2 host | "without having to manage servers or clusters of Amazon EC2 instances" | [AWS Fargate](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/AWS_Fargate.html) |
| Fargate means subnets are meaningful | "the awsvpc network mode is required" | [RegisterTaskDefinition](https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_RegisterTaskDefinition.html) |
| A function's subnets share one VPC, at most 16 | "security groups and subnets in the VPC"; one `VpcId`; 16 items | [`AWS::Lambda::Function`](https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-lambda-function.html), [VpcConfigResponse](https://docs.aws.amazon.com/lambda/latest/api/API_VpcConfigResponse.html), [VpcConfig](https://docs.aws.amazon.com/lambda/latest/api/API_VpcConfig.html) |
| A function is regional, and a zone does not apply | "Lambda runs your function in multiple Availability Zones" | [Resilience](https://docs.aws.amazon.com/lambda/latest/dg/security-resilience.html) |
| A web ACL protects only listed types | "You can protect the following resource types" | [What is AWS WAF](https://docs.aws.amazon.com/waf/latest/developerguide/what-is-aws-waf.html) |
| A regional web ACL shares its resource's Region | "must be in the same region as your resource" | [Associating](https://docs.aws.amazon.com/waf/latest/developerguide/web-acl-associating-aws-resource.html) |
| One web ACL for each resource | "with only one" protection pack (web ACL) | [Associating](https://docs.aws.amazon.com/waf/latest/developerguide/web-acl-associating-aws-resource.html) |

## Calls that could have gone another way

**An ECS cluster refuses a network attachment, although AWS's words are loose here.** The clusters page lists "the network (VPC and subnet) where your tasks and services run" among what a cluster consists of, and the services page says "your cluster VPC". Reference pictures often draw a cluster inside a VPC. But neither CloudFormation nor the cluster's own settings give a cluster a VPC or subnet: the service or task holds that, and the page's own sentence places the network with the tasks and services. S06 reads a type's network form from its real configuration, as it does for S3, so this follows that, and the remedy says where the network belongs. A model that attaches one fails in both modes and is corrected in one step. S06 also says a false rejection is worse than a gap, so this is the one rule here that a reviewer or the owner may reasonably reverse, by changing `network` on that record.

**One WAF type, not two.** A web ACL's `Scope` is `REGIONAL` or `CLOUDFRONT`, which differ in location, and S06 gives product variants their own types where a rule differs. A CloudFront-scope type would have nothing in this catalog to protect, because CloudFront is not in it. So one record stays regional, a region stays optional, and a draft that attaches one to an unknown CloudFront type gets no WAF rule. CloudFront's addition is the time to split it.

**`attachment` and `policy` both count as an association, and `traffic` does not.** Authors often draw users through a WAF to a service. That claims nothing about what the web ACL protects, so it stays free. Both of the other kinds do claim it, so a web ACL on an EC2 instance fails either way and in either direction.

**An EC2 host is allowed on an ECS service only.** A service on EC2 capacity really runs on those instances, so naming them is true. Several instances are not several clusters.

**The core package stays `0.5.0a1`.** A new version would change `uv.lock`, and both plugins name their private runtime by its digest, so every machine would need a new runtime for a catalog addition. Earlier core changes under D-030 also kept the version. The catalog version is what results report for this, and it does change.

## Deliberately not enforced

| Not enforced | Why |
|---|---|
| Five security groups on a workload or function | AWS states it, but the check needs a new field and a diagram with six is rare, so it waits until it matters |
| At least two subnets on a function | AWS advises several zones and does not require them |
| A public or private subnet for Fargate or Lambda | No documented requirement applies to what a model states |
| A workload and its cluster in one account | No statement was verified, and the model can leave either unspecified |
| Which capacity an `aws.containers.ecs_service` uses | The type stays neutral. Use `aws.containers.ecs_fargate` when it is Fargate |

## Icons and rights

All five icons are in the `aws-architecture-icons` pack, which the rights manifest already lists as approved for architecture diagrams. They arrive through the pinned `diagrams` 0.25.1 wheel, and `native_icons.json` locks each file's digest. Nothing is copied into the package, nothing needed a stand-in, and no pack changed. The icons were looked at directly: four are AWS's service icons and `ElasticContainerServiceService` is AWS's ECS service resource icon. Upstream copies may be older than AWS's current set, which FR-048 already discloses.

The picture holds AWS and generic icons only, and a test requires its manifest to say `private_use_only: false`. Huawei's limit under D-018 and O-002 is unchanged. The package and plugins still hold Huawei icons, so they stay private.

## Effects outside the catalog

| Area | Change |
|---|---|
| Catalog version | `2026.11.0` to `2026.11.1` in every catalog file |
| Existing models | Valid models stay valid. No existing type or rule tightened, and only a type that lists targets is limited |
| Catalog search | `ECS` with `--provider aws` now finds three AWS types, and with no provider finds those and Huawei's. FR-054 still holds, because only a provider chooses between them. The skill already asks which one is meant |
| Model guide | States how to place these types |
| Work skill | Its example of a missing service moves from AWS WAF to Amazon CloudFront |
| Reference baselines | Unchanged. `visual-regression` passes with no update, because no renderer code and no reference model changed |
| Claude plugin | Versioned by commit, so a merge reaches it with no bump |
