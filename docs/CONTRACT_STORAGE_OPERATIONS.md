# Lepinguobjektide storage, reconciliation ja taastamine

## Eesmärk

Lepingudokumendid kasutavad Django vaikimisi storage-liidest. Arenduses jääb backend lokaalseks failisüsteemiks. Tootmises saab sama `Contract.document_file` välja suunata S3- või MinIO-ühilduvasse bucket’isse ilma API-tarbijat või andmemudelit muutmata.

## Konfiguratsioon

| Keskkond | Nõutud seaded | Tulemus |
|---|---|---|
| Arendus ja lokaalne testimine | `FORESTIQ_DOCUMENT_STORAGE_BACKEND=local` või seadistus puudub | Failid paiknevad `FORESTIQ_MEDIA_ROOT` kataloogis; vaikimisi `django_backend/media`. |
| S3 või MinIO tootmises | `FORESTIQ_DOCUMENT_STORAGE_BACKEND=s3`, `FORESTIQ_S3_BUCKET_NAME`, `FORESTIQ_S3_ACCESS_KEY`, `FORESTIQ_S3_SECRET_KEY` | Lepingu PDF-id salvestatakse bucket’isse. |
| MinIO või muu S3-ühilduv teenus | Lisaks `FORESTIQ_S3_ENDPOINT_URL`, tavaliselt `FORESTIQ_S3_ADDRESSING_STYLE=path`; vajadusel `FORESTIQ_S3_REGION_NAME` | Kasutatakse antud endpoint’i ja path-style adresseerimist. |

Rakendus ei aktsepteeri `s3` režiimi ilma bucket’i nimeta. Salajased võtmed jäävad keskkonnamuutujatesse ning neid ei tohi lisada Git’i, seed-andmetesse ega management command’i väljundisse.

## Reconciliation

Käsk võrdleb ainult `contracts/` prefiksi objekte `Contract.document_file` andmebaasiviidetega. Vaikimisi on see **dry-run**, mis ei kirjuta ega kustuta midagi.

```bash
cd django_backend
python manage.py reconcile_contract_storage
python manage.py reconcile_contract_storage --organization tenant-slug
```

Raport on JSON ning sisaldab andmebaasis viidatud objekte, puuduvaid objekte, orbusid objekte ning legacy binaardokumente. See sobib lisamiseks käituslogisse või auditi artefaktina muutmistaotlusele.

Parandusrežiimi tuleb käivitada alles pärast dry-run’i ülevaatust.

```bash
python manage.py reconcile_contract_storage --apply
```

Parandusrežiim taastab puuduva nimega objekti ainult juhul, kui lepingu `document` väljal on alles binaarkoopia; migreerib legacy DB-binaari configured storage’i; ning kustutab ainult `contracts/` prefiksi orvuks jäänud objektid. Muude prefiksite objekte ei puudutata. Objekti, millel puudub nii fail kui ka DB-binaarkoopia, ei taastata: käsk lõpetab veaga ja loetleb selle raportis.

## Backup ja taastamisharjutus

Enne storage-backendi, bucket’i, lifecycle-policy või lepingu kustutusreegli muutmist tuleb teha ning säilitada samast ajast pärinev PostgreSQL-i ja lepinguobjektide varukoopia.

```bash
# Andmebaas: asenda ühenduse parameetrid tootmiskeskkonna väärtustega.
pg_dump --format=custom --file=forestiq-contracts-YYYYMMDD.dump "$DATABASE_URL"

# Lokaalne storage: arhiveeri ainult lepingute prefix.
tar -C "$FORESTIQ_MEDIA_ROOT" -czf forestiq-contract-files-YYYYMMDD.tgz contracts

# S3/MinIO: kasuta teenuse heakskiidetud versioonitud bucket-backup’i või sync-käsku.
# Seejärel säilita selle käsu manifest ja checksum’id sama muutmistaotluse juures.
```

Taastamisharjutus toimub alati eraldatud keskkonnas. Taasta kõigepealt andmebaas, seejärel lepinguobjektid samasse konfiguratsiooni. Käivita reconciliation kuivkäiguna, kinnita, et `missingObjects`, `orphanedObjects` ja `unrepairedMissingObjects` on tühjad, ning salvesta JSON-raport koos kuupäeva, andmebaasi dump’i identifikaatori ja objektihoidla manifestiga. Automaattestid katavad puuduva faili taastamise retained DB-binaarist, legacy binaari storage’i migratsiooni, dry-run’i muutmatuse ning orvuobjektide piiratud eemaldamise.
