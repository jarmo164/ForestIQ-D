from tempfile import TemporaryDirectory

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from accounts.models import User
from operations.models import Contract


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
        self.client.force_authenticate(self.user)

    def test_admin_can_store_and_read_local_contract_pdf(self):
        uploaded = SimpleUploadedFile("agreement.pdf", b"%PDF-1.4 test", content_type="application/pdf")
        response = self.client.post(f"/api/services/contracts/{self.contract.id}/document", {"file": uploaded}, format="multipart")
        self.assertEqual(response.status_code, 201, response.data)
        self.contract.refresh_from_db()
        self.assertTrue(self.contract.document_file.name.endswith("contract-contract-test.pdf"))
        pdf = self.client.get(f"/api/services/contracts/{self.contract.id}/pdf")
        self.assertEqual(pdf.status_code, 200)
