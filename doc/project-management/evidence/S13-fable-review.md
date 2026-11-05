# Fable reviews of S13

Date: 2026-11-05 | Change: [S13](S13-aws-next-types.md), `3b692c1` onward on `codex/aws-next-types` | Policy: D-021

Claude Fable 5.1 (`claude-fable-5-1`) reviewed this in an agent with no prior context on the change. **It shares a vendor with the implementer, Claude Opus 5.5, so it reduces shared assumptions and does not remove them.**

**Effort is not established.** The agent was started with a High setting, the project's level for provider semantics, and it said it cannot confirm its own setting. The record therefore states what was asked and no more.

## Passes

| Pass | Reviewed | Ran | Verdict |
|---|---|---|---|
| Review | `3b692c1..4bd7e7d` | The full gate, with 1935 tests and only the stale proof failing, 33 models through the CLI, 6 renders, 9 sabotage changes in a scratch copy and 13 AWS pages fetched | **Approved**, with three P3 findings |

## Findings

| ID | Finding | Severity | State |
|---|---|---|---|
| P3-1 | A repository sat under `compute.containers`, whose meaning did not cover a registry, although `network.routing` had been widened for hosted zones | P3 | Fixed: the meaning now includes registries |
| P3-2 | A node-based cache that states a zone must list only that zone's subnets, although AWS allows one zone on a wider subnet group. This is a false rejection in a narrow case, corrected in one step, and RDS and EC2 read a subnet list the same way | P3 | **Open by choice**, and now stated in S13 and in the model guide: `subnet_refs` means where the nodes attach |
| P3-3 | The record credited all 16 types to the owner's choice, and stated "whatever its endpoint type" as AWS's words when it is an inference | P3 | Fixed in S13 and in the records that repeated the count |

The reviewer also noted, as predating this change, that a type with no `host_types` may name an ECS cluster in `deployment_context` and pass strict, as S3 could before. Nothing here changes it, and it stays open.

## Limits the reviewer stated

- No live session with either plugin, no Work host check, no actual CI and no FR-048 comparison with AWS's current icon set. It did not run `scripts/reproduce_core.py`, as instructed.
- 32 of the 45 new AWS pages were not fetched by the reviewer, including most per-type CloudFormation pages and the DynamoDB, SQS, SNS, KMS, Secrets Manager and ECR pages. Those rest on the patterns in `S06-source-checks.json`.
