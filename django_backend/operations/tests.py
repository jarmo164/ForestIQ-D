from tempfile import TemporaryDirectory

from django.core.files.base import ContentFile
from django.core.files.storage import InMemoryStorage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from accounts.models import User
from api.auth import token_pair
from operations.models import Contract
from operations.services.contract_storage import reconcile_contract_storage


class ContractLocalFileTests(TestCase):
    def setUp(self):
        self.media_dir = TemporaryDirectory()
        self.settings = override_settings(MEDIA_ROOT=self.media_dir.name)
        self.settings.enable()
        self.addCleanup(self.settings.disable)
        self.addCleanup(self.media_dir.cleanup)
        self.user = User.objects.create_superuser("contract-admin", "Contract administrator", "strong-password")
        self.contract = Contract.objects.create(id="contract-test")
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token_pair(self.user)['actualToken']['token']}")

    def test_admin_can_store_and_read_local_contract_pdf(self):
        uploaded = SimpleUploadedFile("agreement.pdf", b"%PDF-1.4 test", content_type="application/pdf")
        response = self.client.post(
            f"/api/services/contracts/{self.contract.id}/document",
            {"file": uploaded, "version": self.contract.version},
            format="multipart",
        )
        self.assertEqual(response.status_code, 201, response.data)
        self.contract.refresh_from_db()
        self.assertTrue(self.contract.document_file.name.endswith("contract-contract-test.pdf"))
        pdf = self.client.get(f"/api/services/contracts/{self.contract.id}/pdf")
        self.assertEqual(pdf.status_code, 200)


class ContractStorageReconciliationTests(TestCase):
    def setUp(self):
        self.storage = InMemoryStorage()
        self.present = Contract.objects.create(id="present-contract")
        self.present.document_file.name = "contracts/2026/01/present.pdf"
        self.present.save(update_fields=("document_file",))
        self.storage.save(self.present.document_file.name, ContentFile(b"%PDF-1.4 present"))

        self.missing = Contract.objects.create(id="missing-contract", document=b"%PDF-1.4 retained")
        self.missing.document_file.name = "contracts/2026/01/missing.pdf"
        self.missing.save(update_fields=("document_file",))

        self.legacy = Contract.objects.create(id="legacy-contract", document=b"%PDF-1.4 legacy")
        self.storage.save("contracts/2026/01/orphan.pdf", ContentFile(b"%PDF-1.4 orphan"))

    def test_dry_run_reports_differences_without_storage_or_database_mutation(self):
        report = reconcile_contract_storage(storage=self.storage)
        self.assertTrue(report.dry_run)
        self.assertEqual(report.missing_objects, [self.missing.document_file.name])
        self.assertEqual(report.orphaned_objects, ["contracts/2026/01/orphan.pdf"])
        self.assertEqual(report.legacy_binary_contracts, [self.legacy.id])
        self.assertFalse(self.storage.exists(self.missing.document_file.name))
        self.legacy.refresh_from_db()
        self.assertFalse(bool(self.legacy.document_file))

    def test_apply_restores_migrates_and_deletes_only_contract_prefix_orphans(self):
        self.storage.save("unrelated/keep.pdf", ContentFile(b"unrelated"))
        report = reconcile_contract_storage(apply=True, storage=self.storage)
        self.assertFalse(report.dry_run)
        self.assertEqual(report.restored_from_database, [self.missing.document_file.name])
        self.assertTrue(self.storage.exists(self.missing.document_file.name))
        self.assertFalse(self.storage.exists("contracts/2026/01/orphan.pdf"))
        self.assertTrue(self.storage.exists("unrelated/keep.pdf"))
        self.legacy.refresh_from_db()
        self.assertTrue(self.legacy.document_file.name.startswith("contracts/"))
        self.assertTrue(self.storage.exists(self.legacy.document_file.name))
