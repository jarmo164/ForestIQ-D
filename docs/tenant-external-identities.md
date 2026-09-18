# Tenant-safe owner and cadastre identities

ForestIQ-D uses **tenant-scoped business identities** while retaining surrogate storage identity compatibility for the existing schema.

## Decision

`Owner.external_id` and `Cadastre.external_id` are the stable public registry identifiers. Existing string primary keys remain internal storage keys so the change does not require rewriting every foreign key in one cutover.

For the first organization that stores a public identifier, the internal primary key may remain equal to the public value. If another organization stores the same public identifier, only its internal primary key is namespaced with the organization UUID. API responses, external integrations, map GeoJSON/MVT properties, cursors intended for clients, and provider requests use `external_id` / `public_id`, never the namespaced storage key.

Uniqueness is enforced by:

- `(organization_id, owner.external_id)`
- `(organization_id, cadastre.external_id)`

Organization-scoped managers continue to fail closed outside a trusted tenant boundary where required.

## Cutover

1. Take a PostgreSQL backup and record the deployed commit.
2. Deploy the application with migration `forestry.0014_tenant_external_identifiers`.
3. The migration widens the internal string PKs, adds `external_id`, backfills it from the existing PK and adds tenant-scoped unique constraints.
4. Validate that every Owner/Cadastre has a non-empty external ID; no duplicate tenant/external-ID pairs exist; detail APIs still return the historical public identifier; MapLibre GeoJSON/MVT contains public cadastre identifiers; and two test tenants can persist the same external identifier.
5. Only after validation allow overlapping multi-tenant registry imports.

Validation queries:

```sql
SELECT organization_id, external_id, COUNT(*)
FROM cadastres
GROUP BY organization_id, external_id
HAVING COUNT(*) > 1;

SELECT organization_id, external_id, COUNT(*)
FROM owners
GROUP BY organization_id, external_id
HAVING COUNT(*) > 1;

SELECT COUNT(*) FROM cadastres WHERE external_id = '';
SELECT COUNT(*) FROM owners WHERE external_id = '';
```

## Rollback

Before overlapping identifiers have been imported, application rollback is safe after restoring the pre-cutover database backup or reversing migration 0014.

After two organizations have stored the same public identifier, **do not reverse 0014 in place**: the old global-PK model cannot represent that state. Restore the pre-cutover backup or export/reconcile the overlapping tenant rows first. This restriction is part of the go/no-go checklist.

## API compatibility

Public Owner/Cadastre IDs remain unchanged. Internal namespaced PKs are an implementation detail. New code must use:

- `obj.public_id` when emitting an identifier or calling an external provider;
- tenant-scoped `id=<public-id>` or explicit `external_id=<public-id>` for business lookups;
- raw `pk` only for internal relational work inside the same tenant.

Vector-tile caches remain keyed by organization and principal; vector properties expose public cadastre identifiers.
