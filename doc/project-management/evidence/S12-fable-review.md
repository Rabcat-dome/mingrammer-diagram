# Fable reviews of S12

Date: 2026-11-05 | Change: [S12](S12-aws-ecs-lambda-waf.md), `a4bf065` onward on `codex/aws-ecs-fargate-lambda-waf` | Policy: D-021

Three passes by Claude Fable 5.1 (`claude-fable-5-1`), each in an agent with no prior context on this change. The first requested changes. The second and third approved. **They share a vendor with the implementer, Claude Opus 5.5, so they reduce shared assumptions and do not remove them.**

**Effort is not established.** Both agents were started with a High setting, the project's level for semantic work. The first reported "low-to-medium effort as set by the session", which does not match, and the second said it cannot see its setting. The record therefore states what was asked and no more.

## Passes

| Pass | Reviewed | Ran | Verdict |
|---|---|---|---|
| Review | `a4bf065..6a9e58a` | 1660 tests, 20 constructed models, each negative case's full error list, 9 AWS pages fetched | **Changes requested** |
| Recheck | `c6c7490..d85d0cf`, after the merge of `main` | 1708 tests, models through the CLI in strict and lenient mode, a hybrid render, 6 AWS pages fetched | **Approved**, with four new P3 findings |
| Follow-up | `d85d0cf..501a1f1`, and that `501a1f1..fe1e472` changes nothing in `src` | 1712 tests, seven further probes | **Approved** |

## Findings

| ID | Finding | Severity | State |
|---|---|---|---|
| P2-1 | An ECS service could not name an on-premises host, though [ECS Anywhere](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/ecs-anywhere.html) registers them to a cluster | P2 | Fixed: both on-premises types are in `host_types`, and Fargate still refuses them |
| P2-2 | In lenient mode a host of an unknown type turned a draft into a failure, against the contract | P2 | Fixed: an unknown host gets no host rule. This also applies to an on-premises VM's hypervisor |
| P3-1 | One web ACL with no declared region could protect ALBs in two regions | P3 | Fixed |
| P3-2 | `AWS_WAF_ACL_MULTIPLE` pointed at whichever edge came second | P3 | Fixed: it names the resource |
| P3-3 | A `policy` edge from IAM to a web ACL was refused | P3 | Fixed: only `attachment` claims what a web ACL protects |
| P3-4 | `attachment_targets` is generic, while its two follow-on codes are AWS's | P3 | **Open by choice**, with a code comment. A second type that lists targets must decide |
| P3-5 | Three negative cases failed for two reasons | P3 | Fixed. All 36 cases on this fixture now fail for one reason, as a separate run showed. The harness still asserts only that the expected code is present, so nothing guards this |
| P3-6 | The requirements' catalog version, the decision log's date and a missing review section | P3 | Fixed |
| P3-A | A service naming an on-premises host may still list VPC subnets, or an EC2 host as well, which AWS does not support | P3 | **Open by choice**: disclosed in S12 and in the model guide, because S06 prefers a gap to a false rejection |
| P3-B | The region mismatch's count and position depended on edge order | P3 | Fixed: once, on the web ACL |
| P3-C | An edge between two web ACLs was refused twice | P3 | Fixed |
| P3-D | The activity log had no S12 entry | P3 | Fixed |

## Limits the reviewers stated

- No live session with either plugin, and no Work host check. Nor did any pass run the whole gate or actual CI.
- Seven of the 16 AWS pages were fetched by neither pass. Their quotes rest on the patterns in `S06-source-checks.json`.
- Two older negative cases, `aws-alb-one-subnet` and `gcp-firewall-two-networks`, also fail for two reasons. They predate this change and are left alone.
