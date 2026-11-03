# S09 ChatGPT Work Acceptance Check

Target: the separate ChatGPT Work page or mode, not Codex (D-014). Automated checks and rehearsals stay in the [S09 evidence](S09-work-plugin.md), and only what the owner reports below counts as a Work result.

**Status: waiting for the owner. Nothing below has been run in Work yet, so M5 stays open.**

## What the owner runs

Install, from a checkout of `codex/s09-work-plugin`, with the commands in the [plugin README](../../../plugins/cloud-architecture-work/README.md#install). Then restart the ChatGPT app, switch to Work mode, open a new chat and select **Cloud Architecture Diagrams**. The S04 plugin stays enabled and unchanged.

Each prompt runs in the same chat unless it says otherwise.

| # | Prompt | What it checks |
|---|---|---|
| 1 | `Use Cloud Architecture Diagrams. Check that its runtime is ready, set it up if it is not, and tell me the plugin version, the runtime state, whether rendering is available and any blockers.` | Install, discovery, approval prompt, setup, version |
| 2 | `Draw an AWS three-tier web application: an Application Load Balancer, two EC2 app servers and an RDS database in one VPC. Show me the picture and give me all six files.` | Rendering, preview, retrieval |
| 3 | `In that diagram, add an S3 bucket that both app servers read from, and draw it again. Keep everything else as it is. Tell me which IDs you kept and added.` | Edit flow, stable IDs, updated source |
| 4 | `Validate this model and tell me what is wrong, without fixing it: {"schema_version":"1.0.0","metadata":{"id":"x","title":"X","environment":"prod","assumptions":[]},"resources":[{"id":"app","name":"App","provider":"aws","service_type":"aws.compute.ec2","taxonomy":"compute.vm"}],"relationships":[{"id":"r1","source_ref":"app","target_ref":"ghost","kind":"traffic"}],"views":[{"id":"v","title":"V","entity_refs":["app"]}]}` | Invalid input: expects `REFERENCE_MISSING` and no image |
| 5 | In Thai, ask for a GKE architecture with a Deployment, Service, Ingress and PVC, with both an overview view and a detail view, and with Thai names on the labels. The session that started this check gives the exact sentence, because repository documents stay English | Kubernetes overview and detail, Thai labels, same IDs in both views |

## Result

| Check | Result |
|---|---|
| Plugin visible and selectable in Work | Pending |
| Version the chat reports | Pending |
| An approval prompt for `setup_runtime`, and what it looked like | Pending |
| Runtime reaches `ready` | Pending |
| PNG visible in the chat, and how it appeared | Pending |
| All six files open from Work | Pending |
| Edit keeps IDs and returns the updated source | Pending |
| Invalid model gives `REFERENCE_MISSING` and no image | Pending |
| Kubernetes overview and detail both draw, with readable Thai | Pending |
| Anything unexpected | Pending |
