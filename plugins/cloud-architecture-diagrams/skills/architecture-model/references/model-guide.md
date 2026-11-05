# Model guide (schema 1.0.0)

A working summary of the contract. The plugin's schema discovery (the `schema` subcommand, or the `get_schema` tool in ChatGPT Work) returns the full JSON Schema and is authoritative when this guide and the validator disagree. It is about 22 KB, so read it only when this guide is not enough.

## Top level

```json
{
  "schema_version": "1.0.0",
  "metadata": {"id": "demo", "title": "Example", "environment": "production", "assumptions": []},
  "scopes": [],
  "boundaries": [],
  "resources": [{"id": "app", "name": "Application", "provider": "aws", "service_type": "aws.compute.ec2", "taxonomy": "compute.vm"}],
  "relationships": [],
  "views": [{"id": "overview", "title": "Overview", "entity_refs": ["app"]}]
}
```

Unknown fields fail everywhere. At least one view is required. The input limit is 1 MiB, 1000 combined scopes/boundaries/resources, 4000 relationships and 32 views.

- **IDs:** lowercase, start with a letter, then letters, digits, `.`, `_` or `-`, at most 64 characters. Scope, boundary, resource, relationship and view IDs share one namespace, so each must be unique across all five.
- **Text:** English and Thai are both fine. Names and labels are 1-256 characters with no control characters, so no newlines. Whatever a view draws must be in the bundled fonts, so `render` refuses `→`, `✓`, `≥`, emoji and scripts the fonts lack, such as Chinese, Japanese and Korean, with `RENDER_TEXT_UNDRAWABLE`. Write `to`, `>=` or words instead; `-`, `>`, `–`, `—` and `…` are fine.
- **Provider:** `aws`, `azure`, `gcp`, `huawei`, `onprem` or `external`. Use `external` for users, the Internet, partners and SaaS.

## Scopes: administrative ownership

`{id, name, provider, kind, parent_ref?}`. Kinds: `account`, `tenant`, `subscription`, `resource_group`, `organization`, `folder`, `project`, `iam_project`, `enterprise_project`, `environment`. A parent must be a scope with the same provider.

## Boundaries: geography, network, security, physical

`{id, name, provider, kind, scope_refs?, parent_ref?, relations?}`. Kinds: `region`, `zone`, `network`, `subnet`, `security_zone`, `security_group`, `site`, `data_center`, `room`, `rack`, `vlan`, `vrf`, `cluster`, `environment`.

`relations` holds `{kind, target_ref}` with kind `located_in`, `network_member_of`, `security_member_of` or `deployment_member_of`. Containment and each relation kind reject cycles.

A boundary's provider and kind resolve to one catalog type, so a boundary needs no `service_type`. `security_group` is the AWS security group, Azure NSG or Huawei security group; GCP has none, because a VPC firewall rule is the resource `gcp.security.vpc_firewall_rule`. `security_zone` is a logical trust zone. Physical kinds are on-premises only, and a logical VLAN cannot be contained by a rack.

| Where | Network | Subnet | Also |
|---|---|---|---|
| AWS | Regional | One zone: `located_in` a zone | A subnet's zone must match its network's region |
| Azure | Regional | Regional, spans zones | A resource attaches only within its subscription and region |
| GCP | Global: no `parent_ref` region and no `located_in` | Regional: `located_in` a region | A Shared VPC workload's project differs from the network's: add an `attachment` relationship from the service project to the host project |
| Huawei Cloud | Regional | Regional | An IAM project maps to one region. Enterprise projects are separate and span regions. Bind a project with the region's `scope_refs` |
| On-premises | Logical | Logical: `network_member_of` a VLAN, VRF or network | `site` > `data_center` > `room` > `rack` is physical. A VM has no `rack_ref`; its `deployment_context` names the `onprem.compute.hypervisor` |

## Resources

`{id, name, provider, service_type, taxonomy, placement?, properties?, kubernetes?}`

- `service_type` is an exact ID from the plugin's catalog search (the `catalog` subcommand, or the `search_catalog` tool in ChatGPT Work), for example `aws.compute.ec2`. It must belong to the resource's provider, and no provider is ever substituted. Keep the provider's native service name in `name`. Strict mode rejects an unknown ID; lenient mode warns and marks a draft.
- `taxonomy` is the one primary ID the catalog shows for that type, and a mismatch fails in both modes. The frozen IDs are: `governance.scope`, `location.site`, `onprem.facility`, `network.boundary`, `network.subnet`, `network.routing`, `network.connectivity`, `network.load_balancing`, `edge.delivery`, `compute.vm`, `compute.physical`, `compute.containers`, `compute.serverless`, `application.platform`, `data.relational`, `data.nosql_cache`, `data.analytics_ai`, `storage.object`, `storage.block_file`, `integration.messaging`, `identity.access`, `security.control`, `security.secrets_keys`, `operations.observability`, `operations.backup_dr`, `external.entity`. A shared category never makes two services equivalent.
- External parties use `provider: external` with `external.people.user`, `external.network.internet`, `external.organization.partner`, `external.service.saas` or `external.system.other`.
- `properties` is closed: `replicas`, `labels`, `service_type` (Kubernetes Service type: `ClusterIP`, `NodePort`, `LoadBalancer` or `ExternalName`), `ports` (`{port, target_port?, protocol?}`, with `protocol` one of `TCP`, `UDP` or `SCTP`).

### Placement keeps dimensions separate

Each dimension is independent. Do not encode one through another: a multi-subnet load balancer lists every subnet, and a Shared VPC workload can sit in a project that does not own the network.

| Field | Must reference |
|---|---|
| `scope_refs` | Scopes with the same provider as the resource |
| `location.region_ref`, `zone_ref`, `site_ref`, `rack_ref` | Boundary of kind `region`, `zone`, `site`, `rack`, with the resource's provider |
| `network_attachments[].network_ref` | Boundary of kind `network` |
| `network_attachments[].subnet_refs` | Boundaries of kind `subnet` |
| `security_boundaries` | Boundaries of kind `security_zone` or `security_group`, the latter with the resource's provider |
| `deployment_context` | Boundaries or resources |

Each type's catalog record states which of these apply (an omitted `location` means any and an omitted `network` means none), and the validator enforces only what you declare, so an unspecified zone or subnet stays valid while a contradictory one fails. Examples: an ALB or EKS cluster that lists subnets needs at least two in different zones, an S3 bucket takes no network attachment, IAM takes no location, and a regional NAT gateway attaches to a VPC while a zonal one sits in one subnet.

On AWS, an ECS cluster and a WAF web ACL take no network attachment. An ECS service, a Fargate workload or a Lambda function holds the network instead: subnets from one VPC, at most 16, and a function may have none. Name the ECS cluster in the workload's `deployment_context`, and an EC2 host or an on-premises server too for a service on that capacity, but never for Fargate. Associate a web ACL with an ALB through an `attachment` relationship, in one region and with one web ACL for each ALB.

Labels follow the platform's syntax: Kubernetes rules on a Kubernetes resource, otherwise AWS tags, Azure tags or GCP labels. Huawei Cloud and on-premises labels are not syntax-checked.

## Relationships

`{id, source_ref, target_ref, kind, direction?, label?, protocol?, purpose?, security?}`. Kinds: `traffic`, `vpn`, `peering`, `replication`, `management`, `membership`, `scheduling`, `policy`, `storage`, `configuration`, `attachment`, `ownership`, `dependency`, `observability`. `direction` is `directed` (default) or `undirected`.

An edge states what was modeled, not proven reachability. Include only connectivity the user described or accepted. Traffic and replication cycles are allowed; ownership cycles are not.

## Views

`{id, title, entity_refs, relationship_refs?, grouping?, direction?, style?, legend?}`

- Selection is explicit, and a selected relationship needs both endpoints selected.
- `grouping`: `none`, `provider` (default), `scope`, `network`, `namespace`, `node`, `physical`. `direction`: `TB` or `LR` (default). `style`: `provider` (default) or `neutral`.
- Each view's unselected IDs come back in `view_exclusions`, with a `VIEW_EXCLUSIONS` warning for each partial view; this is disclosure, not a failure. `excluded_ids` repeats the list for the first view or the one named by `--view`.

### Choosing what a view selects

A view reads best when it selects only the boxes its grouping can draw. Give one `provider` view by default, and add another only when the user asks or when a fact needs its own picture.

| `grouping` | Use it for | Draws as boxes |
|---|---|---|
| `provider` | The main solution view | Scopes, boundaries, and Kubernetes clusters, node pools and namespaces |
| `network` | Network membership | Networks, subnets, VLANs and VRFs |
| `physical` | Placement by region, zone, site or rack | Regions, zones, sites, data centers, rooms and racks |
| `scope` | Ownership apart from the network | Scopes |
| `namespace` | Kubernetes logical detail | Kubernetes clusters, node pools and namespaces |
| `node` | Kubernetes worker placement detail | Kubernetes clusters, node pools and Nodes |
| `none` | A flat picture | Nothing |

- **Use `namespace` or `node` for Kubernetes detail.** Only these list a resource's declared `properties` on its node, and its typed references such as `secret_refs`, `config_refs` and `service_account_ref` where no selected relationship draws them. A `provider` overview leaves them out and stays compact.
- **Leave out what the grouping cannot draw.** Any other selected scope or boundary becomes a loose labeled box. A `network` view, for example, should not select a region or a zone.
- **Leave out zone boxes in a `provider` view.** A subnet nests under its network, so a zone box stays empty. A declared subnet, zone or rack is noted on each resource even when the view does not select it, so the fact stays. Use a `physical` view when the user wants resources drawn by zone.
- **Select a region only where it can hold something**, as in `provider` and `physical` views. Elsewhere it would be a loose box, and leaving it out also drops its note.
- **State an account once.** Selecting a scope without nesting repeats a `scope:` note on every resource. Where it is true, give the outermost boundary the same `scope_refs`, such as the region an account uses, and the account box then holds it. A resource or boundary that declares a scope never nests inside a different one.
- **Keep ownership apart.** If showing a project or resource group would imply that it owns the network, leave it out of the network view and add a `scope` view.
- **Split rather than crowd.** Keep each view to about 40 entities. Show a Kubernetes cluster compactly in the cloud view, and give its detail a `namespace` view and a `node` view.
- **Choose the direction from the picture.** `LR` suits a flow through a few tiers. Use `TB` when `LR` makes one long column, and for Kubernetes detail.

A view of one account's web tier, and a second view by zone, as the `views` list:

```text
[
  {"id": "overview", "title": "Web application", "grouping": "provider", "direction": "TB",
   "entity_refs": ["account", "region", "vpc", "subnet-a", "subnet-b", "alb", "web-a", "web-b", "db"],
   "relationship_refs": ["alb-web-a", "alb-web-b", "web-a-db", "web-b-db"]},
  {"id": "zones", "title": "By Availability Zone", "grouping": "physical", "direction": "TB",
   "entity_refs": ["region", "az-a", "az-b", "alb", "web-a", "web-b", "db"],
   "relationship_refs": ["alb-web-a", "alb-web-b", "web-a-db", "web-b-db"]}
]
```

## Kubernetes context

Kubernetes is a platform inside a hosting provider, not a provider value. A resource carries `kubernetes: {kind, ...}` and keeps its real `provider`. `service_type` must match the kind: `k8s.<lowercase kind>`, for example `k8s.pod` with taxonomy `compute.containers`, except where a provider type below maps the kind. The catalog gives each kind's taxonomy and its Kubernetes API version, verified against release 1.37.

| Cluster type (kind `Cluster`) | Control plane | Node-pool types (kind `NodePool`) |
|---|---|---|
| `k8s.cluster` | User managed | `k8s.nodepool` |
| `onprem.containers.kubernetes_cluster` | User managed | `k8s.nodepool` |
| `aws.containers.eks` | Provider managed | `aws.containers.eks_managed_node_group`, `aws.containers.eks_self_managed_nodes`, `aws.containers.eks_fargate_profile`, `k8s.nodepool` |
| `aws.containers.eks_auto_mode` | Provider managed; nodes are abstracted | Same as `aws.containers.eks` |
| `azure.containers.aks` | Provider managed | `azure.containers.aks_node_pool`, `k8s.nodepool` |
| `azure.containers.aks_automatic` | Provider managed; nodes are abstracted | Same as `azure.containers.aks` |
| `gcp.containers.gke_standard` | Provider managed | `gcp.containers.gke_node_pool`, `k8s.nodepool` |
| `gcp.containers.gke_autopilot` | Provider managed; nodes are abstracted | None |
| `huawei.containers.cce_standard`, `huawei.containers.cce_turbo` | Provider managed | `huawei.containers.cce_node_pool`, `k8s.nodepool` |
| `huawei.containers.cce_autopilot` | Provider managed; nodes are abstracted | None |

A provider-managed `ControlPlane` is a logical marker and takes no location or network attachment. Declaring a `Node` in an abstracted mode returns a `K8S_ABSTRACTED_NODE_DECLARED` warning: keep it only if the node was supplied.

Kinds: `Cluster`, `ControlPlane`, `NodePool`, `Node`, `Namespace`, `Deployment`, `ReplicaSet`, `StatefulSet`, `DaemonSet`, `Job`, `CronJob`, `Pod`, `Service`, `Ingress`, `IngressController`, `PersistentVolumeClaim`, `PersistentVolume`, `StorageClass`, `ConfigMap`, `Secret`, `ServiceAccount`, `NetworkPolicy`.

- `Cluster` has no `cluster_ref`; every other kind requires one, in the same provider.
- Cluster-scoped kinds forbid `namespace_ref`: `Cluster`, `ControlPlane`, `NodePool`, `Node`, `Namespace`, `PersistentVolume`, `StorageClass`.
- All other kinds require `namespace_ref`, except `IngressController`, where it is optional.

| Field | Allowed on | Must target |
|---|---|---|
| `node_pool_ref` | `Node` | `NodePool` |
| `node_ref` | `Pod` | `Node` |
| `owner_ref` | `ReplicaSet`, `Job`, `Pod` | `Deployment` for a `ReplicaSet`; `CronJob` for a `Job`; `ReplicaSet`, `StatefulSet`, `DaemonSet` or `Job` for a `Pod`; same namespace |
| `service_refs` | `Ingress` | `Service`, same namespace |
| `target_refs` | `Service` | `Pod`, same namespace |
| `volume_ref` | `PersistentVolumeClaim` | `PersistentVolume` |
| `storage_class_ref` | `PersistentVolumeClaim`, `PersistentVolume` | `StorageClass` |
| `volume_claim_refs` | `Pod` or workload kind | `PersistentVolumeClaim`, same namespace |
| `config_refs` | `Pod`, workload kind or `IngressController` | `ConfigMap`, same namespace |
| `secret_refs` | `Pod`, workload kind, `ServiceAccount`, `Ingress` or `IngressController` | `Secret`, same namespace |
| `service_account_ref` | `Pod` or workload kind | `ServiceAccount`, same namespace |

An `ownership` relationship pointing at a Kubernetes resource follows the same matrix as `owner_ref`, so a Deployment owns a ReplicaSet, not a Pod directly. Use `management` for a looser link. A source that is an administrative scope must have the same provider.

Relationship kinds between Kubernetes resources stay distinct:

| Kind | Source | Target |
|---|---|---|
| `scheduling` | `Pod` or workload kind | `Node` or `NodePool` |
| `membership` | A resource in that scope | `Cluster`, its own `Namespace`, or a `NodePool` for a `Node` |
| `policy` | `NetworkPolicy` | `Pod`, workload kind or `Namespace`, same namespace |
| `storage` | `Pod`, workload kind, `PersistentVolumeClaim` or `PersistentVolume` | `PersistentVolumeClaim`, `PersistentVolume` or `StorageClass` |
| `configuration` | `Pod`, workload kind, `ServiceAccount`, `Ingress` or `IngressController` | `ConfigMap`, `Secret` or `ServiceAccount`, same namespace |
| `traffic` | Any except the kinds listed below | Any except the kinds listed below |

`traffic` cannot touch `Namespace`, `ConfigMap`, `Secret`, `ServiceAccount`, `StorageClass`, `NetworkPolicy`, `PersistentVolumeClaim`, `PersistentVolume` or `NodePool`. An external load balancer the user supplied links to a Service with a `traffic` relationship, and an `Ingress` and its `IngressController` are separate resources, linked with `management`.

`replicas` applies to `Deployment`, `ReplicaSet` and `StatefulSet`; `service_type` to `Service`; `ports` to Pods, workloads, `Service`, `Ingress` and `IngressController`. An `ExternalName` Service lists no `target_refs`.

A namespace is logical grouping and does not place a Pod on a Node, so `deployment_context` cannot name a `Node` or `NodePool`. Leave `node_ref` unset when placement was not supplied; missing placement is valid, while invented placement is not. Do not model hidden managed control-plane machines or node pools the user did not describe. `Secret` resources cannot carry `properties`.
