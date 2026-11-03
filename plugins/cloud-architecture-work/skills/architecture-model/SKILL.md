---
name: architecture-model
description: Author, edit, validate and draw a canonical cloud architecture model as versioned JSON, with stable IDs, explicit assumptions and separate ownership, location, network, security and deployment dimensions. Use whenever the user wants to design, describe, review, change or draw a solution architecture on AWS, Azure, GCP, Huawei Cloud, on-premises, hybrid or multi-cloud, or a detailed Kubernetes architecture (cluster, node pool, namespace, workload, Service, Ingress, storage), in English or Thai, even if they only say "architecture diagram". Do not use it for flowcharts or other non-infrastructure diagrams.
---

# Architecture model

Turn an architecture request into a reviewable JSON model, check it, and draw it with this plugin's tools: `get_capabilities`, `setup_runtime`, `get_schema`, `search_catalog`, `validate_model`, `render_model`, `read_artifact` and `list_bundles`. The JSON is the source of truth: the renderer draws from it, and later edits build on it, so a correct small model beats a complete-looking guess.

## Calling the tools

These are MCP tools on the server `cloud-architecture`. In a chat where tools run through the JavaScript `exec` tool, call them as `tools.mcp__cloud_architecture__render_model({model})`, and the same way for the others. They may be left out of `exec`'s description, but they are always in `ALL_TOOLS`. Each returns `{content, isError}`:

- `content[0].text` is the JSON answer, so parse it with `JSON.parse` and print what you need with `text(...)`.
- After `render_model` with `status` `ok`, `content[1]` is the image, unless `preview` says it was left out because it is too large. `read_artifact` on the PNG returns it the same way. Pass it to `image(...)`, or you will not see the picture. On any other status there is no `content[1]`.
- After `read_artifact` on a JSON file, `content[1].resource.text` is the file.

Writing a model takes many tokens, so write it once: keep it with `store("model", model)` and read it back with `load("model")` in later `exec` calls.

Every answer's `status` says what happened, with `code`, `message` and `remedy` on anything but `ok`:

| `status` | Meaning | What to do |
|---|---|---|
| `ok` | It worked. Details are in `result` | Continue |
| `validation_failed` | The model is invalid, or this view cannot be drawn as asked | Fix the model by its diagnostics, or split the view |
| `runtime_failure` | This run failed and published nothing | Relay the remedy; do not treat it as a fault in the model |
| `timeout` | The run was stopped at its time limit and published nothing | Split the view into smaller views |
| `artifact_unavailable` | A bundle or file cannot be read, or a bundle did not check out | Relay the remedy, and render again if it says to |
| `runtime_unavailable` | The private runtime is not ready | Follow step 1 |
| `invalid_arguments` | The tool call itself was wrong | Correct the call |
| `busy` | Another render is running | Wait for it, then call again |

## What this version can do

`get_capabilities` is authoritative. A validated model passed the core, catalog and documented provider rules. That does not prove that anything is deployed, that traffic is reachable, that a policy is enforced or that a controller is available. A rule fires only on what the model declares, so a missing zone or Pod placement stays unspecified. Say so whenever you report a result, because the user may otherwise treat it as architecture approval.

If rendering is unavailable or fails, say so and offer the validated model. Do not fill the gap by writing `diagrams` Python, Graphviz DOT, Mermaid or other generated code, and do not use another diagram or image tool: an image made outside the controlled renderer skips its checks and approved icons. PDF and DOT export and automatic overview/detail generation do not exist.

The plugin's tools run on this Mac, so they work only in a chat that runs locally. If its tools are not available in this chat, say that rather than simulating them.

### Huawei Cloud icons

Huawei Cloud service icons are accepted by the owner for private personal use only. Their rights are not cleared, so any model using them returns one `ASSET_PRIVATE_USE_ONLY` warning, and a rendered bundle that shows them states the same limit in its `rights` and in the image. Report it, and do not suggest publishing the output or sharing it outside private use.

If a type returns `ICON_UNAVAILABLE`, it has no usable icon, and `render_model` refuses it in both modes with `RENDER_TYPE_BLOCKED`. Keep its native service name, and never propose a generic symbol or an icon pack found elsewhere as a stand-in.

## Workflow

1. **Check the runtime.** Call `get_capabilities` once, and report `result.plugin.version` when the user asks about setup or versions. Read `result.runtime.state`:
   - `ready`: continue, and look at `result.blockers`. A blocker with a remedy, such as installing Graphviz, stops drawing but not validation. Relay it. If `result.runtime.render_probe.passed` is false, rendering failed when setup last ran: relay its `codes`, and call `setup_runtime` again once their cause is fixed.
   - `not_installed`, or `failed` once its cause is fixed: tell the user the first run downloads Python packages, call `setup_runtime` once, and then call `get_capabilities` every 15 to 30 seconds until the state changes. The app may ask the user to approve the call, because it reaches the network. If the call is refused, give the user `result.setup_command` to run in Terminal, and check again when they say it has finished. Do not install anything yourself.
   - `installing`: keep checking in the same way.
   - `failed`: relay `result.runtime.failure`.
   A `PLUGIN_UPDATED` code means this chat holds an old version of the plugin: tell the user to open a new chat.
2. **Understand the request.** Identify the providers and environment. Ask about uncertainty that changes the architecture's meaning, such as whether "ECS" means AWS or Huawei Cloud. Record smaller working choices in `metadata.assumptions`. Do not add resources, security controls or connectivity the user did not ask for; offer them as labeled suggestions and include them only once accepted.
3. **Look up exact types.** Call `search_catalog`, for example with `provider` `aws` and `query` `load balancer`, to find a `service_type`, its one `taxonomy` ID and its placement rule. `list_taxonomy` lists the taxonomy IDs. Never guess an ID. Unknown types fail in strict mode. The catalog holds a minimum set of services, so one the user names may be missing, such as AWS WAF. Say so and let the user choose; the honest option is often a lenient draft with the real service name, which step 6 explains.
4. **Author the JSON.** Read [references/model-guide.md](references/model-guide.md) before writing a model, and use [examples/core-valid.json](examples/core-valid.json) or [examples/kubernetes-valid.json](examples/kubernetes-valid.json) as a shape to follow. Choose each view's `grouping` and selection from the guide's section on choosing what a view selects, because a selected box its grouping cannot draw comes out as a loose box. A Kubernetes request usually needs an overview view and at least one detail view of the same entities.
5. **Validate.** Call `validate_model` with the whole model as `model`. One call checks every view and lists each view's excluded IDs in `result.view_exclusions`; `view` only chooses which one `selected_view` and `excluded_ids` describe. On `validation_failed`, the diagnostics are in `result.diagnostics`.
6. **Fix by diagnostic.** Each diagnostic gives a `code`, a `field` path and a `remedy`. Correct the model; do not delete a requested component or relationship to make validation pass. If a request cannot be expressed, tell the user. `mode` `lenient` marks a draft and turns only an unknown `service_type` into a disclosed warning, keeping the provider, type and label. It bypasses no other error, so it is not a way past a failure.
7. **Render, when the user wants a picture.** Call `render_model` with `model`, adding `view` to pick a view; the first view is the default. Each call validates again and draws one view into a new bundle, so call it once per view, one at a time. For another view of a model you have just rendered, pass the earlier `bundle_id` instead of `model`, which avoids sending the model again. Only `status` `ok` means a bundle exists. Look at the attached PNG before you report: check that labels are readable and that nothing requested is missing. A `RENDER_PNG_SCALED` warning means the PNG was shrunk to fit, so tell the user and point to `diagram.svg`, which keeps full size. `RENDER_VIEW_TOO_LARGE`, `RENDER_PIXEL_LIMIT` and `RENDER_PNG_SCALE_LIMIT` mean the view must be split; the pixel limit applies to the full-size image, so it can refuse a view inside the entity limit. In `lenient` mode the image and manifest are marked DRAFT, and an unknown type is drawn with the approved generic symbol; never present that as a final diagram.
8. **Report.** State what was modeled, the assumptions, the validation result, any warnings and the pending checks. Disclose the IDs listed for every view in `view_exclusions`, since a partial view must never silently drop a component. If you rendered, show the picture as a Markdown image whose target is the full `path` of `diagram.png`, and link all six files from `result.artifacts` as Markdown links to their full paths: `diagram.png`, `diagram.svg`, `model.json`, `view.json`, `diagnostics.json` and `manifest.json`. Relay `result.rights`, including any private-use limit and draft marking. Otherwise state that no image was produced.

## Editing an existing model

Start from the bundle's source: call `read_artifact` with its `bundle_id` and `file` `model.json`, or use `list_bundles` first if the bundle is not in this chat. Keep existing IDs, including those of unrelated resources and relationships, so diffs and future diagrams stay comparable. Change only what was asked, tell the user what changed, then validate and render again. A render never changes an earlier bundle, so the new `model.json` is the updated source, and the earlier bundle stays as it was.

## Data the model must not contain

Do not place secret values, credentials or real tokens anywhere in the model. A Kubernetes `Secret` resource is a reference marker with no properties; the name is fine, the payload is not.

The tool calls and their results, including the model and local file paths, are part of this chat, like anything else sent to the model the user selected. The plugin sends none of this anywhere else. Only setup reaches the network, to download packages. Rendering has no network access, and bundles stay in the folder `get_capabilities` names.
