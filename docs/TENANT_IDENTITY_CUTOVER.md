# Tenant identity cutover plan

## Decision

ForestIQ-D will move `Owner` and `Cadastre` from globally keyed business identifiers to tenant-owned records with surrogate primary keys and stable public identifiers.

Chosen model: **tenant-based objects with surrogate primary keys**.

The current public identifiers stay as external identifiers:

- `Owner.external_identifier` keeps the legacy owner identifier now stored in `Owner.id`.
- `Cadastre.external_identifier` keeps the public cadastre number now stored in `Cadastre.id`.
- Each table enforces `(organization_id, external_identifier)` uniqueness.
- API payloads, map properties, imports and cursor tokens keep using the stable external identifiers until an explicitly versioned API cutover is released.

This avoids cross-tenant write conflicts without introducing a global canonical-owner data-sharing model. Workflow state, contact details, assignments, offers, contracts, map cache and audit rows remain fully tenant-owned.

## Why not global canonical objects

Global canonical owners/cadastres would require a separate authorization layer for organization-specific rights, workflow state and contact enrichment. The current rewrite already models every business row as organization-scoped, so tenant-owned objects are the smallest safe change and match the existing isolation model.

## Target schema

### `owners`

- `pk` UUID primary key, generated per tenant-owned record.
- `external_identifier` string, populated from the old `id` value.
- `legacy_id` compatibility alias only during transition if required by API serializers.
- Unique constraint: `(organization_id, external_identifier)`.
- Indexes: `(organization_id, external_identifier)`, `(organization_id, status)`, `(organization_id, assignee)`.

### `cadastres`

- `pk` UUID primary key, generated per tenant-owned record.
- `external_identifier` string, populated from the old `id` value and containing the public cadastre number.
- Unique constraint: `(organization_id, external_identifier)`.
- Indexes: `(organization_id, external_identifier)`, `(organization_id, county, municipality)`.

### Tenant-owned relationships

Every foreign key must point to the surrogate primary key after cutover. Public identifiers may be denormalized for read-only map/search responses, but not used as relational primary keys.

Affected relationship families:

- `OwnerCadastre.owner`, `OwnerCadastre.cadastre`
- `OwnerLog.owner`
- `CadastreLabel.cadastre`
- `CadastreSubPart.cadastre`
- `CadastreNotification.cadastre`
- `ForestRegistryFeature.cadastre`
- `OwnerFollowing.owner`
- `DataSyncRun.cadastre`
- `InheritanceSignal.owner`, `InheritanceSignal.cadastre`
- P1/P2 operation models that reference owners, cadastres, deals, workbaskets, evidence snapshots or owner relations
- MVT/cache invalidation keys and map feature properties

## Migration phases

### Phase 0: guards before schema cutover

1. Keep existing primary keys unchanged.
2. Add tests that document the current unsafe behavior: two organizations cannot persist the same `Owner.id` or `Cadastre.id`.
3. Add an executable cutover checklist and require it before enabling production migration.

### Phase 1: additive schema

1. Add nullable `surrogate_id` UUID columns to `owners` and `cadastres`.
2. Add nullable `external_identifier` columns.
3. Backfill:
   - `surrogate_id = gen_random_uuid()` for every row.
   - `external_identifier = id` for owners and cadastres.
4. Add non-unique indexes for `(organization_id, external_identifier)`.
5. Add validation queries that prove no duplicate `(organization_id, external_identifier)` pairs exist before enforcing constraints.

### Phase 2: dual-write compatibility

1. Imports write by `(organization_id, external_identifier)` and never by global `id` alone.
2. API lookup helpers accept external identifiers, resolve them inside the active organization and return 404 when the record exists only in another tenant.
3. MVT and GeoJSON queries scope every cache key with `organization_id` and resolve public identifiers through the tenant row.
4. Cursor tokens include the external identifier and, when needed, the surrogate id version.

### Phase 3: foreign-key cutover

1. Add new FK columns beside existing FK columns for every affected relationship.
2. Backfill new FK columns by joining old identifiers within the same organization.
3. Add validation queries for missing or cross-tenant joins.
4. Switch ORM fields and import services to the new FK columns.
5. Keep read-only compatibility aliases for API v1.

### Phase 4: primary-key swap

1. Lock writes for the affected tables during the cutover window.
2. Promote surrogate UUID columns to primary keys.
3. Rename old identifier columns to `external_identifier` where still needed.
4. Enforce `(organization_id, external_identifier)` unique constraints.
5. Run the tenant-isolation regression suite and map tile/cache negative tests.

### Phase 5: cleanup

1. Remove obsolete old-FK columns after one successful release cycle.
2. Drop compatibility aliases only in a versioned API release.
3. Keep external identifiers in all user-facing payloads.

## Rollback strategy

Rollback is allowed until Phase 4 begins.

- Phase 1 rollback: drop additive columns and indexes.
- Phase 2 rollback: disable dual-write code path and keep old global PK behavior.
- Phase 3 rollback: switch ORM fields back to old FK columns; keep additive columns for diagnosis.
- Phase 4 rollback: restore from pre-cutover backup. This phase must be treated as a database cutover and requires a verified backup and a write freeze.

## Required validation queries

Before enforcing constraints:

```sql
select organization_id, id, count(*)
from owners
group by organization_id, id
having count(*) > 1;

select organization_id, id, count(*)
from cadastres
group by organization_id, id
having count(*) > 1;
```

Before FK cutover:

```sql
select oc.*
from owner_cadastre oc
left join owners o on o.organization_id = oc.organization_id and o.id = oc.owner_id
left join cadastres c on c.organization_id = oc.organization_id and c.id = oc.cadastre_id
where o.id is null or c.id is null;
```

Before map/cache release:

- Generate the same cadastre external identifier in two organizations.
- Request owner detail, cadastre detail, MVT tile, GeoJSON feature collection and workbasket API from both organizations.
- Assert no response contains the other organization's workflow fields, contacts, assignments, cached tile payload or registry projections.

## API compatibility

API v1 must continue to expose `ownerId` and `cadastreId` as the public external identifiers. Internal surrogate keys must not leak into API v1 URLs unless a new `/api/v2` route is introduced.

Recommended lookup pattern:

```python
Owner.objects.get(external_identifier=owner_id)
Cadastre.objects.get(external_identifier=cadastre_id)
```

The organization-scoped manager must be active for all API, task and import code paths before using these lookups.

## Operational checklist

1. Backup production database.
2. Run duplicate validation queries.
3. Run additive migrations.
4. Backfill external identifiers and surrogate UUIDs.
5. Enable dual-write feature flag in staging.
6. Run tenant-isolation tests with duplicate identifiers.
7. Run MVT/cache negative tests.
8. Freeze writes.
9. Run FK cutover and primary-key swap.
10. Run smoke tests for imports, owner detail, cadastre detail, map tiles and workbaskets.
11. Unfreeze writes.
12. Keep rollback backup until one full import and one daily delta cycle have completed successfully.
