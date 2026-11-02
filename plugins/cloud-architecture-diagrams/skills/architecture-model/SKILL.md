---
name: architecture-model
description: Author, edit and validate a canonical cloud architecture model as versioned JSON, with stable IDs, explicit assumptions and separate ownership, location, network, security and deployment dimensions. Use whenever the user wants to design, describe, review or change a solution architecture on AWS, Azure, GCP, Huawei Cloud, on-premises, hybrid or multi-cloud, or a detailed Kubernetes architecture (cluster, node pool, namespace, workload, Service, Ingress, storage), in English or Thai, even if they only say "architecture diagram". This version validates the model against provider catalogs and placement rules but cannot render SVG or PNG images yet; do not use it for flowcharts or other non-infrastructure diagrams.
allowed-tools: Bash("${CLAUDE_PLUGIN_ROOT}/bin/cloud-diagrams" *)
---

# Architecture model

Turn an architecture request into a reviewable JSON model and check it with this plugin's command, `"${CLAUDE_PLUGIN_ROOT}/bin/cloud-diagrams"`. Run it by that quoted full path, because the plugin's `bin` folder is not reliably on the Bash path, and run it on its own with nothing chained after it, because this skill pre-approves only this command. The JSON is the source of truth: the future renderer draws from it, and later edits build on it, so a correct small model beats a complete-looking guess.

## What this version can do

The `capabilities` subcommand is authoritative. At this version:

- **Implemented:** schema and catalog discovery, plus strict structural, identity, reference, cycle, view, Kubernetes context, catalog, provider placement and Kubernetes semantic validation.
- **Not implemented:** SVG/PNG rendering.

A `"valid": true` result therefore means the model passed the core, catalog and documented provider rules (`validation_scope: core_catalog_provider`). It does not prove that anything is deployed, that traffic is reachable, that a policy is enforced or that a controller is available, and it does not render a picture. A rule fires only on what the model declares, so a missing zone or Pod placement stays unspecified. Say so whenever you report a result, because the user may otherwise treat it as architecture approval.

If the user asks for a picture, say this version cannot render one and offer the validated model. Do not fill the gap by writing `diagrams` Python, Graphviz DOT or other generated code to execute: the project accepts architecture input as data only, and an image made outside the controlled renderer would skip its checks and approved icons.

### Huawei Cloud icons

No Huawei Cloud service icon is approved, because the rights are unresolved (open decision O-002). Huawei models validate fully, and each service type returns an `ASSET_RIGHTS_BLOCKED` warning. Report that warning. Keep the native service name, and never propose a generic symbol or an icon pack found elsewhere as a stand-in.

## Workflow

1. **Check the runtime.** Run `"${CLAUDE_PLUGIN_ROOT}/bin/cloud-diagrams" capabilities` once. The first run may download Python dependencies. Exit code 3 means the runtime could not be prepared or failed unexpectedly: relay the stderr message rather than installing packages yourself. Exit code 64 means the command was used incorrectly, so check the usage message on stderr.
2. **Understand the request.** Identify the providers and environment. Ask about uncertainty that changes the architecture's meaning, such as whether "ECS" means AWS or Huawei Cloud. Record smaller working choices in `metadata.assumptions`. Do not add resources, security controls or connectivity the user did not ask for; offer them as labeled suggestions and include them only once accepted.
3. **Look up exact types.** Run `"${CLAUDE_PLUGIN_ROOT}/bin/cloud-diagrams" catalog --provider aws --query "load balancer"` to find a `service_type`, its one `taxonomy` ID and its placement rule. Filters are `--provider`, `--entity`, `--taxonomy`, `--query`, `--type`, `--kubernetes` and `--limit`, and `--taxonomy-list` lists the taxonomy IDs. Never guess an ID. Unknown types fail in strict mode.
4. **Author the JSON.** Read [references/model-guide.md](references/model-guide.md) before writing a model, and use [examples/core-valid.json](examples/core-valid.json) or [examples/kubernetes-valid.json](examples/kubernetes-valid.json) as a shape to follow. Save the model with the Write tool where the user can keep it, for example `architecture/<metadata.id>.json`.
5. **Validate.** Run `"${CLAUDE_PLUGIN_ROOT}/bin/cloud-diagrams" validate < architecture/model.json`. One run checks every view and lists each view's excluded IDs in `view_exclusions`; `--view <id>` only chooses which view `selected_view` and `excluded_ids` describe. The `valid` field in the JSON gives the outcome. Exit 0 means valid; exit 2 means invalid, with the diagnostics on stdout.
6. **Fix by diagnostic.** Each diagnostic gives a `code`, a `field` path and a `remedy`. Correct the model; do not delete a requested component or relationship to make validation pass. If a request cannot be expressed, tell the user. `--mode lenient` marks a draft and turns only an unknown `service_type` into a disclosed warning, keeping the provider, type and label. It bypasses every other error, so it is not a way past a failure.
7. **Report.** State what was modeled, the assumptions, the validation result, any warnings and the pending checks. Disclose the IDs listed for every view in `view_exclusions`, since a partial view must never silently drop a component. State that no image was produced.

## Editing an existing model

Change the same file and keep existing IDs, including those of unrelated resources and relationships, so diffs and future diagrams stay comparable. Tell the user what changed, then validate again.

## Data the model must not contain

Do not place secret values, credentials or real tokens anywhere in the model. A Kubernetes `Secret` resource is a reference marker with no properties; the name is fine, the payload is not.
