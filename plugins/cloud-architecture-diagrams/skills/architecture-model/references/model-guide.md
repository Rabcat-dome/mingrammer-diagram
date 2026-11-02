# Model guide (schema 1.0.0)

A working summary of the contract. The plugin command's `schema` subcommand prints the full JSON Schema and is authoritative when this guide and the validator disagree. It is about 22 KB, so read it only when this guide is not enough.

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
- **Text:** English and Thai are both fine. Names and labels are 1-256 characters with no control characters, so no newlines.
- **Provider:** `aws`, `azure`, `gcp`, `huawei`, `onprem` or `external`. Use `external` for users, the Internet, partners and SaaS.

## Scopes: administrative ownership

`{id, name, provider, kind, parent_ref?}`. Kinds: `account`, `tenant`, `subscription`, `resource_group`, `organization`, `folder`, `project`, `iam_project`, `enterprise_project`, `environment`. A parent must be a scope with the same provider.

## Boundaries: geography, network, security, physical

`{id, name, provider, kind, scope_refs?, parent_ref?, relations?}`. Kinds: `region`, `zone`, `network`, `subnet`, `security_zone`, `site`, `data_center`, `room`, `rack`, `vlan`, `vrf`, `cluster`, `environment`.

`relations` holds `{kind, target_ref}` with kind `located_in`, `network_member_of`, `security_member_of` or `deployment_member_of`. Containment and each relation kind reject cycles.

## Resources

`{id, name, provider, service_type, taxonomy, placement?, properties?, kubernetes?}`

- `service_type` uses the ID format, for example `aws.compute.ec2`. No catalog resolves these yet, so treat them as provisional and keep the provider's native service name in `name`.
- `taxonomy`: use one of these IDs: `governance.scope`, `location.site`, `onprem.facility`, `network.boundary`, `network.subnet`, `network.routing`, `network.connectivity`, `network.load_balancing`, `edge.delivery`, `compute.vm`, `compute.physical`, `compute.containers`, `compute.serverless`, `application.platform`, `data.relational`, `data.nosql_cache`, `data.analytics_ai`, `storage.object`, `storage.block_file`, `integration.messaging`, `identity.access`, `security.control`, `security.secrets_keys`, `operations.observability`, `operations.backup_dr`. Until catalogs arrive, the validator checks only that an ID has two dot-separated parts, so it will not catch a wrong ID.
- `properties` is closed: `replicas`, `labels`, `service_type` (Kubernetes Service type: `ClusterIP`, `NodePort`, `LoadBalancer` or `ExternalName`), `ports` (`{port, target_port?, protocol?}`, with `protocol` one of `TCP`, `UDP` or `SCTP`).

### Placement keeps dimensions separate

Each dimension is independent. Do not encode one through another: a multi-subnet load balancer lists every subnet, and a Shared VPC workload can sit in a project that does not own the network.

| Field | Must reference |
|---|---|
| `scope_refs` | Scopes with the same provider as the resource |
| `location.region_ref`, `zone_ref`, `site_ref`, `rack_ref` | Boundary of kind `region`, `zone`, `site`, `rack` |
| `network_attachments[].network_ref` | Boundary of kind `network` |
| `network_attachments[].subnet_refs` | Boundaries of kind `subnet` |
| `security_boundaries` | Boundaries of kind `security_zone` |
| `deployment_context` | Boundaries or resources |

## Relationships

`{id, source_ref, target_ref, kind, direction?, label?, protocol?, purpose?, security?}`. Kinds: `traffic`, `vpn`, `peering`, `replication`, `management`, `membership`, `scheduling`, `policy`, `storage`, `configuration`, `attachment`, `ownership`, `dependency`, `observability`. `direction` is `directed` (default) or `undirected`.

An edge states what was modeled, not proven reachability. Include only connectivity the user described or accepted. Traffic and replication cycles are allowed; ownership cycles are not.

## Views

`{id, title, entity_refs, relationship_refs?, grouping?, direction?, style?, legend?}`

- Selection is explicit, and a selected relationship needs both endpoints selected.
- `grouping`: `none`, `provider` (default), `scope`, `network`, `namespace`, `node`, `physical`. `direction`: `TB` or `LR` (default). `style`: `provider` (default) or `neutral`.
- Each view's unselected IDs come back in `view_exclusions`, with a `VIEW_EXCLUSIONS` warning for each partial view; this is disclosure, not a failure. `excluded_ids` repeats the list for the first view or the one named by `--view`.

## Kubernetes context

Kubernetes is a platform inside a hosting provider, not a provider value. A resource carries `kubernetes: {kind, ...}` and keeps its real `provider`, and `service_type` should follow `k8s.<kind>`, for example `k8s.pod` with taxonomy `compute.containers`. The validator does not check this match yet.

Kinds: `Cluster`, `ControlPlane`, `NodePool`, `Node`, `Namespace`, `Deployment`, `ReplicaSet`, `StatefulSet`, `DaemonSet`, `Job`, `CronJob`, `Pod`, `Service`, `Ingress`, `IngressController`, `PersistentVolumeClaim`, `PersistentVolume`, `StorageClass`, `ConfigMap`, `Secret`, `ServiceAccount`, `NetworkPolicy`.

- `Cluster` has no `cluster_ref`; every other kind requires one, in the same provider.
- Cluster-scoped kinds forbid `namespace_ref`: `Cluster`, `ControlPlane`, `NodePool`, `Node`, `Namespace`, `PersistentVolume`, `StorageClass`.
- All other kinds require `namespace_ref`, except `IngressController`, where it is optional.

| Field | Allowed on | Must target |
|---|---|---|
| `node_pool_ref` | `Node` | `NodePool` |
| `node_ref` | `Pod` | `Node` |
| `owner_ref` | Any | Workload kind or `Pod`, same namespace |
| `service_refs` | `Ingress` | `Service`, same namespace |
| `target_refs` | `Service` | `Pod`, same namespace |
| `volume_ref` | `PersistentVolumeClaim` | `PersistentVolume` |
| `storage_class_ref` | `PersistentVolumeClaim`, `PersistentVolume` | `StorageClass` |
| `volume_claim_refs` | Any | `PersistentVolumeClaim`, same namespace |
| `config_refs` | Any | `ConfigMap`, same namespace |
| `secret_refs` | Any | `Secret`, same namespace |
| `service_account_ref` | Any | `ServiceAccount`, same namespace |

An `ownership` relationship pointing at a Kubernetes resource follows the same rule as `owner_ref`: its source must be a workload kind or `Pod` in the same cluster and namespace. A source that is an administrative scope must have the same provider.

A namespace is logical grouping and does not place a Pod on a Node. Leave `node_ref` unset when placement was not supplied; missing placement is valid, while invented placement is not. Do not model hidden managed control-plane machines or node pools the user did not describe. `Secret` resources cannot carry `properties`.
